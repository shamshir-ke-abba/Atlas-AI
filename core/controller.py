"""
Atlas V3 Controller

Central application controller.

Responsibilities:
- Manage application state
- Manage conversations
- Manage AIService
- Synchronize AtlasBrain with the active conversation
- Route user messages to the AI service
- Publish AI events to the EventBus
- Keep GUI/backend state synchronized
"""

from datetime import datetime

from core.logger import logger
from core.state import AtlasState
from core.profile_store import ProfileStore
from core.conversation import (
    ConversationStore,
    ConversationManager,
)
from core.ai_service import AIService
from core.events import (
    MessageReceived,
    ChunkReceived,
    ThinkingStarted,
    ThinkingFinished,
    ErrorOccurred,
)
from agents.coding.permissions import CodingPermissions
from agents.coding.detector import CodingTaskDetector


class Controller:
    """
    Central controller for Atlas V3.

    Architecture:

        GUI
          |
          v
        Controller
          |
          +---- ConversationStore
          |
          +---- AIService
                    |
                    v
                  AIWorker
                    |
                    v
                AtlasBrain
                    |
                    +---- Tools
                    +---- Model
    """

    def __init__(
        self,
        bus,
        state=None,
        tools=None,
        memory=None,
    ):

        self.bus = bus
        self.gui_parent = None

        # --------------------------------------------------
        # State
        # --------------------------------------------------

        if state is None:
            state = AtlasState()

        self.state = state

        # --------------------------------------------------
        # Persistent Atlas profile
        # --------------------------------------------------

        self.profile_store = ProfileStore()

        # --------------------------------------------------
        # Conversation storage
        # --------------------------------------------------

        self.conversations = ConversationStore()

        # --------------------------------------------------
        # AI service
        # --------------------------------------------------

        self.ai = AIService(
            bus=self.bus,
            state=self.state,
        )

        # --------------------------------------------------
        # Connect shared profile to the loaded tools
        # --------------------------------------------------

        tool_manager = getattr(
            self.ai,
            "tools",
            None,
        )

        if tool_manager is not None:
            attach = getattr(
                tool_manager,
                "attach_profile_store",
                None,
            )

            if callable(attach):
                attach(self.profile_store)

        # --------------------------------------------------
        # AI service signals
        # --------------------------------------------------

        self.ai.chunk_ready.connect(
            self._handle_ai_chunk
        )

        self.ai.finished.connect(
            self._handle_ai_finished
        )

        self.ai.error.connect(
            self._handle_ai_error
        )

        # --------------------------------------------------
        # User message event
        # --------------------------------------------------

        self.bus.subscribe(
            MessageReceived,
            self._handle_message_received,
        )

        # --------------------------------------------------
        # Ensure active conversation
        # --------------------------------------------------

        self._ensure_active_conversation()

        # --------------------------------------------------
        # Synchronize brain
        # --------------------------------------------------

        self._sync_brain()

        logger.info(
            "Controller initialized"
        )

        self.coding_detector = CodingTaskDetector()

        self.ai.coding_result.connect(
            self._handle_coding_result
        )

        self.ai.coding_error.connect(
            self._handle_coding_error
        )

        self.ai.coding_finished.connect(
            self._handle_coding_finished
        )

    # ======================================================
    # PERSISTENT PROFILE
    # ======================================================

    def get_profile(self):
        """Return a copy of the complete persistent Atlas profile."""

        return self.profile_store.get_profile()

    def get_profile_value(
        self,
        path,
        default=None,
    ):
        """Read a nested profile value using dot notation."""

        return self.profile_store.get(
            path,
            default,
        )

    def set_profile_value(
        self,
        path,
        value,
    ):
        """Set and persist one profile value."""

        self.profile_store.set(
            path,
            value,
        )

    def update_profile(
        self,
        values,
    ):
        """Merge structured data into the persistent profile."""

        self.profile_store.update(
            values
        )

    def update_profile_section(
        self,
        section,
        values,
    ):
        """Update one section of the persistent profile."""

        self.profile_store.update_section(
            section,
            values,
        )

    def reset_profile(self):
        """Reset the persistent Atlas profile to defaults."""

        self.profile_store.reset()

    # ======================================================
    # CONVERSATION HELPERS
    # ======================================================

    def _conversation_metadata(
        self,
        conversation_id,
    ):
        """
        Return metadata for a conversation.
        """

        if not conversation_id:
            return None

        conversations = (
            self.conversations.list_all()
        )

        if not isinstance(
            conversations,
            dict,
        ):
            return None

        return conversations.get(
            conversation_id
        )

    # ------------------------------------------------------

    def _get_latest_conversation_id(
        self,
    ):
        """
        Find the newest conversation safely.

        Handles missing/None timestamps without
        allowing max() to compare None and strings.
        """

        conversations = (
            self.conversations.list_all()
        )

        if not conversations:
            return None

        if not isinstance(
            conversations,
            dict,
        ):
            return None

        best_id = None
        best_time = ""

        for conversation_id, metadata in conversations.items():

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            modified = (
                metadata.get("modified")
                or metadata.get("created")
                or ""
            )

            # Always convert to string so comparison
            # between None and str cannot happen.
            modified = str(
                modified
            )

            if (
                best_id is None
                or modified > best_time
            ):
                best_id = conversation_id
                best_time = modified

        return best_id

    # ======================================================
    # ENSURE ACTIVE CONVERSATION
    # ======================================================

    def _ensure_active_conversation(
        self,
    ):
        """
        Ensure there is always an active conversation.
        """

        active_id = (
            self.state.active_conversation_id
        )

        # --------------------------------------------------
        # Existing active conversation still exists
        # --------------------------------------------------

        if active_id:

            manager = (
                self.conversations.load(
                    active_id
                )
            )

            if manager is not None:

                logger.info(
                    "Using active conversation: %s",
                    active_id,
                )

                return active_id

        # --------------------------------------------------
        # Try newest existing conversation
        # --------------------------------------------------

        latest_id = (
            self._get_latest_conversation_id()
        )

        if latest_id:

            manager = (
                self.conversations.load(
                    latest_id
                )
            )

            if manager is not None:

                self.state.active_conversation_id = (
                    latest_id
                )

                logger.info(
                    "Restored latest conversation: %s",
                    latest_id,
                )

                return latest_id

        # --------------------------------------------------
        # Nothing exists -> create one
        # --------------------------------------------------

        return self.create_conversation(
            synchronize=False
        )

    # ======================================================
    # CREATE
    # ======================================================


    def create_conversation(
        self,
        synchronize=True,
    ):
        """
        Create a new conversation.

        An untouched active "New Chat" is reused so repeated clicks on
        New Chat cannot create a pile of empty conversations.
        """
        import uuid

        active_id = self.get_active_conversation_id()
        if active_id:
            active = self.get_active_conversation()
            if (
                active is not None
                and not active.get_messages()
                and str(getattr(active, "title", "")) == "New Chat"
            ):
                if synchronize:
                    self._sync_brain()
                return active_id

        conversation_id = str(uuid.uuid4())
        manager = ConversationManager(
            conversation_id=conversation_id,
            title="New Chat",
        )

        if not self.conversations.save(manager):
            logger.error(
                "Failed to create conversation: %s",
                conversation_id,
            )
            return None

        self.state.active_conversation_id = conversation_id
        self.state.current_message = ""
        self.state.current_response = ""
        self.state.status = "Idle"
        self.state.is_generating = False

        if hasattr(self.state, "stop_event"):
            self.state.stop_event.clear()

        if synchronize:
            self._sync_brain()

        logger.info("Created conversation: %s", conversation_id)
        return conversation_id

    # ======================================================
    # GET ACTIVE ID
    # ======================================================

    def get_active_conversation_id(
        self,
    ):

        return (
            self.state.active_conversation_id
        )

    # ======================================================
    # GET ACTIVE CONVERSATION
    # ======================================================

    def get_active_conversation(
        self,
    ):
        """
        Return the active ConversationManager.
        """

        conversation_id = (
            self.get_active_conversation_id()
        )

        if not conversation_id:
            return None

        return (
            self.conversations.load(
                conversation_id
            )
        )

    # ======================================================
    # GET CONVERSATIONS
    # ======================================================

    def get_conversations(
        self,
    ):
        """
        Return conversations in the format expected
        by the sidebar.

        The sidebar supports a list of dictionaries,
        so return that format.
        """

        conversations = (
            self.conversations.list_all()
        )

        result = []

        if not isinstance(
            conversations,
            dict,
        ):
            return result

        for conversation_id, metadata in conversations.items():

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            result.append(
                {
                    "id": conversation_id,
                    "title": (
                        metadata.get("title")
                        or "New Chat"
                    ),
                    "created": (
                        metadata.get("created")
                    ),
                    "modified": (
                        metadata.get("modified")
                    ),
                    "message_count": (
                        metadata.get(
                            "message_count",
                            0,
                        )
                    ),
                }
            )

        # --------------------------------------------------
        # Newest conversations first
        # --------------------------------------------------

        result.sort(
            key=lambda item: str(
                item.get("modified")
                or item.get("created")
                or ""
            ),
            reverse=True,
        )

        return result

    # ======================================================
    # LOAD
    # ======================================================

    def load_conversation(
        self,
        conversation_id,
    ):
        """
        Load a conversation and synchronize AtlasBrain.
        """

        if not conversation_id:
            return False

        manager = (
            self.conversations.load(
                conversation_id
            )
        )

        if manager is None:

            logger.warning(
                "Conversation not found: %s",
                conversation_id,
            )

            return False

        self.state.active_conversation_id = (
            conversation_id
        )

        self.state.current_message = ""
        self.state.current_response = ""

        self.state.status = "Idle"
        self.state.is_generating = False

        if hasattr(
            self.state,
            "stop_event",
        ):

            self.state.stop_event.clear()

        self._sync_brain()

        logger.info(
            "Loaded conversation: %s",
            conversation_id,
        )

        return True

    # ======================================================
    # RENAME
    # ======================================================

    def rename_conversation(
        self,
        conversation_id,
        new_title,
    ):
        """
        Rename a conversation.
        """

        if not conversation_id:
            return False

        if not new_title:
            return False

        new_title = str(
            new_title
        ).strip()

        if not new_title:
            return False

        success = (
            self.conversations.rename(
                conversation_id,
                new_title,
            )
        )

        if success:

            logger.info(
                "Renamed conversation %s -> %s",
                conversation_id,
                new_title,
            )

        return success

    # ======================================================
    # DELETE
    # ======================================================


    def delete_conversation(
        self,
        conversation_id,
    ):
        """Delete a conversation without spawning duplicate empty chats."""
        if not conversation_id:
            return False

        if self.state.is_generating:
            logger.warning(
                "Refusing to delete while Atlas is generating."
            )
            return False

        active_id = self.get_active_conversation_id()
        was_active = str(active_id) == str(conversation_id)

        if not self.conversations.delete(conversation_id):
            return False

        if was_active:
            remaining = self.conversations.list_all()
            candidates = []

            if isinstance(remaining, dict):
                for cid, meta in remaining.items():
                    if not isinstance(meta, dict):
                        meta = {}
                    modified = str(
                        meta.get("modified")
                        or meta.get("created")
                        or ""
                    )
                    candidates.append((modified, str(cid)))

            candidates.sort(reverse=True)

            if candidates:
                self.state.active_conversation_id = candidates[0][1]
                self._sync_brain()
            else:
                self.state.active_conversation_id = None
                self.create_conversation(synchronize=True)
        else:
            self._sync_brain()

        return True


    # ======================================================
    # INTERACTIVE TOOL PROFILE SETUP
    # ======================================================

    @staticmethod
    def _profile_setup_tool(message):
        text = str(message or "").lower().strip()

        nutrition_signals = (
            "nutrition", "meal plan", "mealplan", "diet", "food",
            "allerg", "intoleran", "what i eat", "eating",
            "i'm fat", "im fat", "i am fat",
            "i'm skinny", "im skinny", "i am skinny",
        )
        fitness_signals = (
            "gym", "workout", "exercise", "fitness",
            "training", "reps", "sets",
        )

        if any(signal in text for signal in nutrition_signals):
            return "nutrition"
        if any(signal in text for signal in fitness_signals):
            return "fitness"
        return None

    def _profile_needs_setup(self, tool):
        plugin = self.ai.tools.get(tool) if self.ai.tools is not None else None
        if plugin is None:
            return False
        checker = getattr(plugin, "profile_complete", None)
        if callable(checker):
            try:
                return not bool(checker())
            except Exception:
                return True
        return False

    def _handle_profile_setup_request(self, text):
        tool = self._profile_setup_tool(text)
        if tool is None or not self._profile_needs_setup(tool):
            return False

        if tool == "fitness":
            prompt = (
                "Let’s set up your fitness profile first. "
                "I’ll use your experience, goal, equipment and restrictions "
                "to tailor future suggestions."
            )
        else:
            prompt = (
                "Let’s set up a nutrition profile first. "
                "I’ll use age, activity, dietary preferences and allergies "
                "to tailor meal ideas."
            )

        from core.events import ProfileSetupRequested
        self.bus.publish(ProfileSetupRequested(tool=tool, prompt=prompt))
        return True

    def apply_tool_profile(self, tool, profile):
        """Save a GUI profile through the real plugin backend."""
        tool = str(tool or "").strip().lower()
        profile = dict(profile or {})
        plugin = self.ai.tools.get(tool)
        if plugin is None:
            raise ValueError(f"Tool '{tool}' is unavailable.")
        if tool not in ("fitness", "nutrition"):
            raise ValueError(f"Interactive profiles are not supported for '{tool}'.")
        result = plugin.set_profile(**profile)
        from core.events import ProfileSetupCompleted
        self.bus.publish(ProfileSetupCompleted(tool=tool, profile=profile, message=str(result or "")))
        return result

    def run_tool_action(self, tool, action, **kwargs):
        """Execute a concrete fitness/nutrition action from the GUI."""
        tool = str(tool or "").strip().lower()
        plugin = self.ai.tools.get(tool)
        if plugin is None:
            raise ValueError(f"Tool '{tool}' is unavailable.")
        method = getattr(plugin, str(action), None)
        if not callable(method):
            raise ValueError(f"Tool '{tool}' has no action '{action}'.")
        return method(**kwargs)

    # ======================================================
    # AUTO TITLE
    # ======================================================

    @staticmethod
    def _auto_title(text):
        """Create a compact, deterministic title from the first user message."""
        text = " ".join(str(text or "").strip().split())
        if not text:
            return "New Chat"
        text = text.rstrip("?!.,;:")
        replacements = (
            ("please tell me ", ""),
            ("can you ", ""),
            ("could you ", ""),
            ("help me ", ""),
        )
        low = text.lower()
        for prefix, replacement in replacements:
            if low.startswith(prefix):
                text = text[len(prefix):]
                break
        words = text.split()[:7]
        title = " ".join(words).strip()
        if len(title) > 42:
            title = title[:42].rsplit(" ", 1)[0]
        if not title:
            return "New Chat"
        return title[0].upper() + title[1:]

    def _auto_rename_if_needed(self, conversation, first_message):
        if conversation is None:
            return False
        current = str(getattr(conversation, "title", "") or "").strip()
        if current.lower() != "new chat":
            return False
        title = self._auto_title(first_message)
        if title == "New Chat":
            return False
        conversation.title = title
        return bool(self.conversations.save(conversation))

    # ======================================================
    # MESSAGE ROUTING
    # ======================================================

    def _handle_message_received(
        self,
        event,
    ):
        """
        Receive a user message from the GUI,
        save it to the active conversation,
        then send it to AIService.
        """

        # Event classes in Atlas V3 currently carry
        # the message as .text.
        text = getattr(
            event,
            "text",
            None,
        )

        if text is None:

            # Compatibility with possible alternate
            # event attribute names.
            text = getattr(
                event,
                "message",
                None,
            )

        if text is None:
            return

        text = str(
            text
        ).strip()

        if not text:
            return

        profile_tool = self._profile_setup_tool(text)
        # Coding Agent is ON HOLD - do not intercept normal chat


        # --------------------------------------------------
        # Make sure an active conversation exists
        # --------------------------------------------------

        if not self.get_active_conversation_id():

            self.create_conversation()

        conversation = (
            self.get_active_conversation()
        )

        if conversation is None:

            logger.error(
                "Could not get active conversation."
            )

            self.bus.publish(
                ErrorOccurred(
                    "Could not access the active conversation."
                )
            )

            return

        # --------------------------------------------------
        # Save user message
        # --------------------------------------------------

        conversation.add_message(
            sender="User",
            text=text,
            is_user=True,
        )

        self.conversations.save(
            conversation
        )

        # Give the chat a useful name immediately after its first message.
        self._auto_rename_if_needed(conversation, text)

        if profile_tool is not None:
            self.state.current_message = text
            self.state.current_response = ""
            self.state.is_generating = False
            self.state.status = "Idle"
            self._sync_brain()

            if self._handle_profile_setup_request(text):
                return


        # --------------------------------------------------
        # Update state
        # --------------------------------------------------

        self.state.current_message = text
        self.state.current_response = ""

        self.state.is_generating = True
        self.state.status = "Thinking"

        if hasattr(
            self.state,
            "stop_event",
        ):

            self.state.stop_event.clear()

        # --------------------------------------------------
        # Tell GUI/backend that thinking started
        # --------------------------------------------------

        self.bus.publish(
            ThinkingStarted()
        )

        logger.info(
            "Sending message to AI: %s",
            text,
        )

        # --------------------------------------------------
        # IMPORTANT:
        # Send to AIService, not directly to AIWorker.
        #
        # AIService owns the QThread.
        # --------------------------------------------------

        self.ai.generate(
            text
        )

    # ======================================================
    # CODING AGENT
    # ======================================================

    def set_gui_parent(self, parent):
        """Set the GUI parent used for modal dialogs."""
        self.gui_parent = parent

    def _request_coding_permissions(self, parent=None):
        """Show the Coding Agent permission dialog."""

        from gui.widgets.coding_permission_dialog import (
            CodingPermissionDialog,
        )

        dialog = CodingPermissionDialog(
            parent=parent
        )

        from PySide6.QtWidgets import QDialog

        if dialog.exec() != QDialog.Accepted:
            return None

        return CodingPermissions(
            **dialog.permissions()
        )

    def _start_coding_task(self, text):
        """Request permission and start Coding Agent execution."""

        permissions = self._request_coding_permissions(
            parent=None
        )

        if permissions is None:
            self.state.is_generating = False
            self.state.status = "Idle"

            self.bus.publish(
                ChunkReceived(
                    "Coding Agent cancelled."
                )
            )

            self.bus.publish(
                ThinkingFinished()
            )

            return True

        self.state.current_message = text
        self.state.current_response = ""
        self.state.is_generating = True
        self.state.status = "Coding"

        if hasattr(self.state, "stop_event"):
            self.state.stop_event.clear()

        self.bus.publish(
            ThinkingStarted()
        )

        logger.info(
            "Starting Coding Agent task: %s",
            text,
        )

        self.ai.execute_coding(
            text,
            permissions,
            max_attempts=2,
        )

        return True

    def _handle_coding_result(self, result):
        """Convert CodingWorkflowResult into a user-facing response."""

        if result is None:
            message = "Coding Agent returned no result."
        elif getattr(result, "success", False):
            message = (
                "Coding task completed successfully.\n\n"
                f"{getattr(result, 'message', '')}"
            )

            applied = getattr(
                result,
                "applied_changes",
                [],
            )

            if applied:
                message += (
                    "\n\nChanged files:\n"
                    + "\n".join(
                        f"- {path}"
                        for path in applied
                    )
                )

            test_result = getattr(
                result,
                "test_result",
                {},
            )

            if test_result:
                message += (
                    "\n\n"
                    + str(
                        test_result.get(
                            "summary",
                            "",
                        )
                    )
                )

        else:
            message = (
                "Coding Agent could not complete the task.\n\n"
                f"{getattr(result, 'message', '')}"
            )

            error_analysis = getattr(
                result,
                "error_analysis",
                None,
            )

            if error_analysis is not None:
                error_type = getattr(
                    error_analysis,
                    "error_type",
                    "",
                )
                error_message = getattr(
                    error_analysis,
                    "message",
                    "",
                )

                if error_type:
                    message += (
                        f"\n\nError type: {error_type}"
                    )

                if error_message:
                    message += (
                        f"\n{error_message}"
                    )

        self.state.current_response = message

        self.bus.publish(
            ChunkReceived(message)
        )

    def _handle_coding_error(self, error):
        """Handle an unexpected Coding Agent error."""

        message = (
            "Coding Agent error: "
            f"{str(error)}"
        )

        self.state.current_response = message

        self.bus.publish(
            ChunkReceived(message)
        )

    def _handle_coding_finished(self):
        """Finish the controller state after Coding Agent execution."""

        response = str(
            self.state.current_response
            or ""
        ).strip()

        conversation = self.get_active_conversation()

        if conversation is not None and response:
            conversation.add_message(
                sender="Atlas",
                text=response,
                is_user=False,
            )

            self.conversations.save(
                conversation
            )

        self.state.is_generating = False
        self.state.status = "Idle"

        self.bus.publish(
            ThinkingFinished()
        )

        logger.info(
            "Coding Agent execution finished."
        )

    # ======================================================
    # STOP GENERATION
    # ======================================================

    def stop_generation(self):
        """Cooperatively stop the current response without killing Atlas."""
        if not getattr(self.state, "is_generating", False):
            return False

        try:
            if hasattr(self.state, "stop_event"):
                self.state.stop_event.set()
            self.ai.cancel_generation()
            self.state.status = "Stopping"
            logger.info("AI generation stop requested.")
            return True
        except Exception as exc:
            logger.warning("Could not stop AI generation: %s", exc)
            return False

    # ======================================================
    # AI CHUNK
    # ======================================================

    def _handle_ai_chunk(
        self,
        text,
    ):
        """
        Receive AI output from AIService.
        """

        if text is None:
            return

        text = str(
            text
        )

        if not text:
            return

        self.state.current_response += (
            text
        )

        self.state.status = "Generating"

        # --------------------------------------------------
        # Send response to GUI
        # --------------------------------------------------

        self.bus.publish(
            ChunkReceived(
                text
            )
        )

    # ======================================================
    # AI FINISHED
    # ======================================================

    def _handle_ai_finished(
        self,
    ):
        """
        Save the completed AI response.
        """

        response = str(
            self.state.current_response
            or ""
        ).strip()

        conversation = (
            self.get_active_conversation()
        )

        if conversation is not None and response:

            conversation.add_message(
                sender="Atlas",
                text=response,
                is_user=False,
            )

            self.conversations.save(
                conversation
            )

        self.state.is_generating = False
        self.state.status = "Idle"

        self.bus.publish(
            ThinkingFinished()
        )

        logger.info(
            "AI response finished."

        )

    # ======================================================
    # AI ERROR
    # ======================================================

    def _handle_ai_error(
        self,
        error,
    ):
        """
        Handle AI worker errors.
        """

        error = str(
            error
        )

        self.state.is_generating = False
        self.state.status = "Error"

        logger.error(
            "AI error: %s",
            error,
        )

        self.bus.publish(
            ErrorOccurred(
                error
            )
        )

        self.bus.publish(
            ThinkingFinished()
        )

    # ======================================================
    # BRAIN SYNCHRONIZATION
    # ======================================================

    def _sync_brain(
        self,
    ):
        """
        Synchronize AtlasBrain's conversation history
        with the active conversation.
        """

        conversation = (
            self.get_active_conversation()
        )

        if conversation is None:

            logger.warning(
                "Cannot synchronize brain: "
                "no active conversation."
            )

            return

        messages = (
            conversation.get_messages()
        )

        # --------------------------------------------------
        # AIService -> AIWorker -> AtlasBrain
        # --------------------------------------------------

        brain = getattr(
            self.ai.worker,
            "brain",
            None,
        )

        if brain is None:

            logger.warning(
                "Cannot synchronize brain: "
                "AIWorker brain unavailable."
            )

            return

        # --------------------------------------------------
        # Brain API used by Atlas V3
        # --------------------------------------------------

        if hasattr(
            brain,
            "set_conversation_history",
        ):

            try:

                brain.set_conversation_history(
                    messages
                )

            except Exception:

                logger.exception(
                    "Failed to synchronize "
                    "conversation history with brain."
                )

                return

        elif hasattr(
            brain,
            "conversation_history",
        ):

            brain.conversation_history = (
                list(messages)
            )

        logger.info(
            "Brain synchronized with conversation: %s",
            conversation.id,
        )

    # ======================================================
    # START
    # ======================================================

    def start(
        self,
    ):
        """
        Start backend services.
        """

        if self.ai is not None:

            self.ai.start()

        logger.info(
            "Controller started."
        )

    # ======================================================
    # STOP
    # ======================================================

    def stop(
        self,
    ):
        """
        Stop backend services cleanly.
        """

        if self.ai is not None:

            try:

                self.ai.stop()

            except Exception as exc:

                logger.warning(
                    "Error stopping AI service: %s",
                    exc,
                )

        logger.info(
            "Controller stopped."
        )
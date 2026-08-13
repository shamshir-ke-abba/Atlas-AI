"""
Atlas V3 Controller

Central application controller.

Responsibilities:
- Conversation lifecycle
- Conversation history
- AI processing
- Runtime state
- GUI integration
"""

from typing import Dict, Optional, Generator

from core.logger import logger
from core.ai_service import AIService


class Controller:
    """Central controller for Atlas."""

    def __init__(
        self,
        bus=None,
        state=None,
    ):
        self.bus = bus
        self.state = state

        # ==================================================
        # AI SERVICE
        # ==================================================

        self.ai = AIService(
            bus=self.bus,
            state=self.state,
        )

        # ==================================================
        # CONVERSATION SERVICE
        # ==================================================

        from ai.services.conversation_service import (
            ConversationService,
        )

        self.conversations = (
            ConversationService()
        )

    # ==================================================
    # LIFECYCLE
    # ==================================================

    def start(self):
        """Start Atlas."""

        logger.info(
            "Starting Controller..."
        )

        try:
            self.ai.start()

        except Exception:
            logger.exception(
                "Failed to start AI service"
            )

        self._sync_active_conversation()

    def stop(self):
        """Stop Atlas."""

        logger.info(
            "Stopping Controller..."
        )

        try:
            self.ai.stop()

        except Exception:
            logger.exception(
                "Failed to stop AI service"
            )

    # ==================================================
    # CONVERSATIONS
    # ==================================================

    def create_conversation(self) -> str:
        """Create a new conversation."""

        conversation_id = (
            self.conversations.new()
        )

        self._set_active_conversation_id(
            conversation_id
        )

        self.ai.clear_conversation()

        self._reset_state()

        logger.info(
            "Created conversation: %s",
            conversation_id,
        )

        return conversation_id

    def get_conversations(
        self,
    ) -> Dict[str, Dict]:

        return self.conversations.list()

    def get_conversation(
        self,
        conversation_id: str,
    ) -> Optional[Dict]:

        conversations = (
            self.conversations.list()
        )

        return conversations.get(
            conversation_id
        )

    def save_conversation(
        self,
        conversation_id: str,
    ) -> bool:

        if not self.conversations.load(
            conversation_id
        ):
            return False

        return self.conversations.save()

    def rename_conversation(
        self,
        conversation_id: str,
        new_title: str,
    ) -> bool:

        return self.conversations.rename(
            conversation_id,
            new_title,
        )

    def delete_conversation(
        self,
        conversation_id: str,
    ) -> bool:

        success = (
            self.conversations.delete(
                conversation_id
            )
        )

        if success:

            if (
                self.get_active_conversation_id()
                == conversation_id
            ):

                self._set_active_conversation_id(
                    None
                )

                self.ai.clear_conversation()

                self._reset_state()

        return success

    # ==================================================
    # ACTIVE CONVERSATION
    # ==================================================

    def get_active_conversation_id(
        self,
    ) -> Optional[str]:

        if self.state is not None:

            conversation_id = getattr(
                self.state,
                "active_conversation_id",
                None,
            )

            if conversation_id:
                return conversation_id

        return self.conversations.get_id()

    def _set_active_conversation_id(
        self,
        conversation_id,
    ):

        if self.state is not None:

            self.state.active_conversation_id = (
                conversation_id
            )

    # ==================================================
    # HISTORY
    # ==================================================

    def _get_history(
        self,
        conversation_id: str,
    ):

        """
        Get the actual messages stored by
        ConversationService.

        Returns:

        [
            {
                "sender": "You",
                "text": "...",
                ...
            },
            {
                "sender": "Atlas",
                "text": "...",
                ...
            }
        ]
        """

        conversation = (
            self.get_conversation(
                conversation_id
            )
        )

        if not conversation:
            return []

        messages = conversation.get(
            "messages",
            [],
        )

        if not isinstance(
            messages,
            list,
        ):
            return []

        return list(
            messages
        )

    def _sync_ai_conversation(
        self,
        conversation_id: str,
    ):
        """
        Synchronize the exact ConversationService
        history with AIService.
        """

        history = self._get_history(
            conversation_id
        )

        logger.info(
            "Syncing AI history: %d messages",
            len(history),
        )

        self.ai.set_conversation(
            conversation_id,
            history,
        )

    # ==================================================
    # SEND MESSAGE
    # ==================================================

    def send_message(
        self,
        conversation_id: str,
        message: str,
    ) -> str:

        message = str(
            message
        ).strip()

        if not message:

            return (
                "Error: Empty message"
            )

        logger.info(
            "Processing message in conversation %s",
            conversation_id,
        )

        # --------------------------------------------------
        # Load conversation
        # --------------------------------------------------

        if not self.conversations.load(
            conversation_id
        ):

            return (
                "Error: Conversation not found"
            )

        # --------------------------------------------------
        # Active conversation
        # --------------------------------------------------

        self._set_active_conversation_id(
            conversation_id
        )

        # --------------------------------------------------
        # Add USER message
        # --------------------------------------------------

        self.conversations.add_user(
            message
        )

        # --------------------------------------------------
        # IMPORTANT:
        #
        # Fetch conversation AGAIN after adding
        # the user message.
        #
        # This gives AIService the actual stored
        # conversation history.
        # --------------------------------------------------

        self._sync_ai_conversation(
            conversation_id
        )

        # --------------------------------------------------
        # Process AI
        # --------------------------------------------------

        full_response = ""

        try:

            response = (
                self.ai.process_message(
                    message
                )
            )

            if response is not None:

                full_response = str(
                    response
                ).strip()

        except Exception as exc:

            logger.exception(
                "Brain processing failed"
            )

            full_response = (
                f"Error: {exc}"
            )

        # --------------------------------------------------
        # Fallback
        # --------------------------------------------------

        if not full_response:

            full_response = (
                "No response generated"
            )

        # --------------------------------------------------
        # Save Atlas response
        # --------------------------------------------------

        self.conversations.add_assistant(
            full_response
        )

        self.conversations.save()

        # --------------------------------------------------
        # Synchronize history again so the next
        # request sees the latest Atlas response.
        # --------------------------------------------------

        self._sync_ai_conversation(
            conversation_id
        )

        return full_response

    # ==================================================
    # STREAMING
    # ==================================================

    def send_message_stream(
        self,
        conversation_id: str,
        message: str,
    ) -> Generator[str, None, None]:

        message = str(
            message
        ).strip()

        if not message:

            yield (
                "Error: Empty message"
            )

            return

        logger.info(
            "Streaming message in conversation %s",
            conversation_id,
        )

        # --------------------------------------------------
        # Load
        # --------------------------------------------------

        if not self.conversations.load(
            conversation_id
        ):

            yield (
                "Error: Conversation not found"
            )

            return

        # --------------------------------------------------
        # Active
        # --------------------------------------------------

        self._set_active_conversation_id(
            conversation_id
        )

        # --------------------------------------------------
        # User message
        # --------------------------------------------------

        self.conversations.add_user(
            message
        )

        # --------------------------------------------------
        # Sync history
        # --------------------------------------------------

        self._sync_ai_conversation(
            conversation_id
        )

        # --------------------------------------------------
        # Process
        # --------------------------------------------------

        full_response = ""

        try:

            response = (
                self.ai.process_message(
                    message
                )
            )

            if response is not None:

                full_response = str(
                    response
                ).strip()

                if full_response:

                    yield full_response

        except Exception as exc:

            logger.exception(
                "Brain processing failed"
            )

            full_response = (
                f"Error: {exc}"
            )

            yield full_response

        # --------------------------------------------------
        # Fallback
        # --------------------------------------------------

        if not full_response:

            full_response = (
                "No response generated"
            )

        # --------------------------------------------------
        # Save
        # --------------------------------------------------

        self.conversations.add_assistant(
            full_response
        )

        self.conversations.save()

        self._sync_ai_conversation(
            conversation_id
        )

    # ==================================================
    # ACTIVE CONVERSATION SYNC
    # ==================================================

    def _sync_active_conversation(
        self,
    ):

        conversation_id = (
            self.conversations.get_id()
        )

        if conversation_id:

            self._set_active_conversation_id(
                conversation_id
            )

            self._sync_ai_conversation(
                conversation_id
            )

    # ==================================================
    # STATE
    # ==================================================

    def _reset_state(
        self,
    ):

        if self.state is None:
            return

        if hasattr(
            self.state,
            "current_message",
        ):

            self.state.current_message = ""

        if hasattr(
            self.state,
            "current_response",
        ):

            self.state.current_response = ""

        if hasattr(
            self.state,
            "status",
        ):

            self.state.status = "Ready"

        if hasattr(
            self.state,
            "is_generating",
        ):

            self.state.is_generating = False
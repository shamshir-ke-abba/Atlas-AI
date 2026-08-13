"""
Atlas V3 Brain

Central AI orchestration layer.

Responsibilities:
- Build conversation-aware prompts
- Maintain conversation history
- Handle deterministic conversation recall
- Route messages through ToolManager
- Generate normal responses through AtlasModel
- Maintain compatibility with Controller and AIWorker
"""

from typing import Any, Dict, Optional

from core.logger import logger
from ai.model import AtlasModel
from ai.context_builder import ContextBuilder


class AtlasBrain:
    """Central AI orchestration."""

    def __init__(
        self,
        model=None,
        memory=None,
        tools=None,
    ):

        self.model = (
            model
            if model is not None
            else AtlasModel()
        )

        self.memory = memory
        self.tools = tools

        self.active_conversation = None
        self.conversation_history = []

        self.context_builder = ContextBuilder()

        logger.info(
            "AtlasBrain initialized"
        )

        if self.tools is not None:

            try:

                logger.info(
                    "Brain tool system loaded: %s",
                    self.tools.available(),
                )

            except Exception as exc:

                logger.warning(
                    "Could not inspect tool system: %s",
                    exc,
                )

    # ==================================================
    # CONVERSATION
    # ==================================================

    def set_active_conversation(
        self,
        conversation,
    ):

        self.active_conversation = conversation

        self.conversation_history = (
            self._extract_history(
                conversation
            )
        )

        logger.debug(
            "Active conversation updated: %d messages",
            len(
                self.conversation_history
            ),
        )

    # --------------------------------------------------

    def set_conversation_history(
        self,
        history,
    ):

        if history is None:

            self.conversation_history = []

            return

        if isinstance(
            history,
            list,
        ):

            self.conversation_history = list(
                history
            )

            logger.debug(
                "Conversation history set: %d messages",
                len(
                    self.conversation_history
                ),
            )

            return

        self.conversation_history = (
            self._extract_history(
                history
            )
        )

    # --------------------------------------------------

    def get_active_conversation_id(
        self,
    ) -> Optional[str]:

        conversation = (
            self.active_conversation
        )

        if conversation is None:
            return None

        if hasattr(
            conversation,
            "get_id",
        ):

            try:

                result = conversation.get_id()

                if result:
                    return result

            except Exception:
                pass

        conversation_id = getattr(
            conversation,
            "id",
            None,
        )

        if conversation_id:
            return conversation_id

        if isinstance(
            conversation,
            dict,
        ):

            return conversation.get(
                "id"
            )

        return None

    # ==================================================
    # MAIN PROCESSING
    # ==================================================

    def process_message(
        self,
        message: str,
        conversation_history=None,
    ) -> str:

        message = str(
            message
        ).strip()

        if not message:

            return (
                "Error: Empty message"
            )

        logger.info(
            "Brain processing message: %s",
            message,
        )

        try:

            if conversation_history is not None:

                self.set_conversation_history(
                    conversation_history
                )

            # ------------------------------------------
            # Deterministic recall
            # ------------------------------------------

            recall_response = (
                self._handle_conversation_recall(
                    message
                )
            )

            if recall_response is not None:

                self._update_memory(
                    message,
                    recall_response,
                )

                return recall_response

            # ------------------------------------------
            # Context
            # ------------------------------------------

            context = self._build_context(
                message
            )

            # ------------------------------------------
            # Routing
            # ------------------------------------------

            handler = self._route_message(
                message
            )

            # ------------------------------------------
            # Execute
            # ------------------------------------------

            response = handler(
                message,
                context,
            )

            if response is None:

                response = (
                    "No response generated."
                )

            response = str(
                response
            ).strip()

            if not response:

                response = (
                    "No response generated."
                )

            self._update_memory(
                message,
                response,
            )

            return response

        except Exception as exc:

            logger.exception(
                "Brain processing failed"
            )

            return (
                f"Error: {exc}"
            )

    # ==================================================
    # RECALL
    # ==================================================

    def _handle_conversation_recall(
        self,
        message: str,
    ):

        if not self.conversation_history:
            return None

        normalized = " ".join(
            str(message)
            .lower()
            .strip()
            .split()
        )

        recall_phrases = (
            "what did i just tell you",
            "what did i tell you",
            "what did i just say",
            "what did i say",
            "what was my last message",
            "what was the last thing i said",
            "what was the last thing i told you",
            "do you remember what i said",
            "do you remember what i told you",
            "do you remember my last message",
        )

        if not any(
            phrase in normalized
            for phrase in recall_phrases
        ):
            return None

        for msg in reversed(
            self.conversation_history
        ):

            if not isinstance(
                msg,
                dict,
            ):
                continue

            is_user = msg.get(
                "is_user"
            )

            sender = str(
                msg.get(
                    "sender",
                    "",
                )
            ).strip().lower()

            if (
                is_user is True
                or sender in (
                    "you",
                    "user",
                )
            ):

                text = str(
                    msg.get(
                        "text",
                        "",
                    )
                ).strip()

                if text:

                    return (
                        f'You just told me: "{text}"'
                    )

        return (
            "I don't have a previous user message "
            "available in this conversation."
        )

    # ==================================================
    # CONTEXT
    # ==================================================

    def _build_context(
        self,
        current_message: str = "",
    ) -> Dict[str, Any]:

        history = list(
            self.conversation_history
        )

        context = {
            "conversation": (
                self.active_conversation
            ),
            "conversation_history": history,
            "memory": self._get_memory(),
            "prompt": "",
        }

        try:

            context["prompt"] = (
                self.context_builder.build(
                    history,
                    current_message,
                )
            )

        except Exception as exc:

            logger.warning(
                "ContextBuilder failed: %s",
                exc,
            )

            context["prompt"] = (
                self._fallback_prompt(
                    history,
                    current_message,
                )
            )

        return context

    # --------------------------------------------------

    def _fallback_prompt(
        self,
        history,
        current_message,
    ) -> str:

        prompt = (
            "You are Atlas, a local AI assistant.\n\n"
            "Use the conversation history to maintain "
            "context and answer naturally.\n\n"
        )

        if history:

            prompt += (
                "===== CONVERSATION HISTORY =====\n"
            )

            for msg in history:

                if not isinstance(
                    msg,
                    dict,
                ):
                    continue

                sender = str(
                    msg.get(
                        "sender",
                        "Unknown",
                    )
                )

                text = str(
                    msg.get(
                        "text",
                        "",
                    )
                )

                if sender.lower() in (
                    "you",
                    "user",
                ):

                    prompt += (
                        f"User: {text}\n"
                    )

                else:

                    prompt += (
                        f"Atlas: {text}\n"
                    )

            prompt += (
                "===== END CONVERSATION HISTORY =====\n\n"
            )

        prompt += (
            "===== CURRENT USER MESSAGE =====\n"
            f"User: {current_message}\n"
            "===== END CURRENT USER MESSAGE =====\n\n"
            "Atlas:"
        )

        return prompt

    # ==================================================
    # ROUTING
    # ==================================================

    def _route_message(
        self,
        message: str,
    ):

        if self.tools is not None:

            try:

                # --------------------------------------
                # Preferred ToolManager API
                # --------------------------------------

                if hasattr(
                    self.tools,
                    "match",
                ):

                    tool = self.tools.match(
                        message
                    )

                    if tool is not None:

                        logger.info(
                            "ROUTE: TOOL -> %s",
                            getattr(
                                tool,
                                "name",
                                type(tool).__name__,
                            ),
                        )

                        return (
                            lambda msg, ctx:
                            self._run_tool(
                                tool,
                                msg,
                            )
                        )

            except Exception as exc:

                logger.warning(
                    "Tool routing failed: %s",
                    exc,
                )

        logger.info(
            "ROUTE: MODEL"
        )

        return self._generate_response

    # ==================================================
    # TOOL EXECUTION
    # ==================================================

    def _run_tool(
        self,
        tool,
        message: str,
    ) -> str:

        try:

            if not hasattr(
                tool,
                "run",
            ):

                return (
                    "Error: Invalid tool"
                )

            logger.info(
                "Executing tool: %s",
                getattr(
                    tool,
                    "name",
                    type(tool).__name__,
                ),
            )

            # ------------------------------------------
            # Standard Atlas plugin API
            # ------------------------------------------

            try:

                result = tool.run(
                    message
                )

            except TypeError:

                try:

                    result = tool.run(
                        message=message
                    )

                except TypeError:

                    result = tool.run(
                        query=message
                    )

            if result is None:

                return (
                    "No result returned by tool."
                )

            return str(
                result
            ).strip()

        except Exception as exc:

            logger.exception(
                "Tool execution failed"
            )

            return (
                f"Error executing tool: {exc}"
            )

    # ==================================================
    # MODEL
    # ==================================================

    def _generate_response(
        self,
        message: str,
        context: Dict[str, Any],
    ) -> str:

        if self.model is None:

            return (
                "Error: Model not available"
            )

        prompt = context.get(
            "prompt",
            "",
        )

        if not prompt:

            prompt = self._fallback_prompt(
                context.get(
                    "conversation_history",
                    [],
                ),
                message,
            )

        try:

            response_parts = []

            for chunk in self.model.generate(
                prompt,
                stream=True,
            ):

                if chunk is None:
                    continue

                response_parts.append(
                    str(chunk)
                )

            response = "".join(
                response_parts
            ).strip()

            if not response:

                return (
                    "No response generated."
                )

            return response

        except Exception as exc:

            logger.exception(
                "Model generation failed"
            )

            return (
                f"Error generating response: {exc}"
            )

    # ==================================================
    # MEMORY
    # ==================================================

    def _get_memory(
        self,
    ) -> Dict[str, Any]:

        if self.memory is None:
            return {}

        try:

            if hasattr(
                self.memory,
                "all",
            ):

                result = self.memory.all()

                if result is not None:
                    return result

        except Exception as exc:

            logger.warning(
                "Memory retrieval failed: %s",
                exc,
            )

        return {}

    # --------------------------------------------------

    def _update_memory(
        self,
        message: str,
        response: str,
    ):

        if self.memory is None:
            return

        try:

            if hasattr(
                self.memory,
                "remember",
            ):

                try:

                    self.memory.remember(
                        message,
                        response,
                    )

                    return

                except TypeError:

                    try:

                        self.memory.remember(
                            message
                        )

                        return

                    except Exception:
                        pass

            if hasattr(
                self.memory,
                "add",
            ):

                try:

                    self.memory.add(
                        message,
                        response,
                    )

                    return

                except TypeError:
                    pass

        except Exception as exc:

            logger.warning(
                "Memory update failed: %s",
                exc,
            )

    # ==================================================
    # HISTORY
    # ==================================================

    def _extract_history(
        self,
        conversation,
    ):

        if conversation is None:
            return []

        if isinstance(
            conversation,
            list,
        ):

            return list(
                conversation
            )

        if isinstance(
            conversation,
            dict,
        ):

            messages = conversation.get(
                "messages",
                [],
            )

            if isinstance(
                messages,
                list,
            ):

                return list(
                    messages
                )

            return []

        messages = getattr(
            conversation,
            "current_messages",
            None,
        )

        if messages is not None:

            try:
                return list(
                    messages
                )
            except Exception:
                pass

        messages = getattr(
            conversation,
            "messages",
            None,
        )

        if messages is not None:

            try:
                return list(
                    messages
                )
            except Exception:
                pass

        if hasattr(
            conversation,
            "last",
        ):

            try:

                result = conversation.last()

                if result is not None:
                    return list(result)

            except Exception:
                pass

        return []

    # ==================================================
    # STATUS
    # ==================================================

    def status(
        self,
    ) -> Dict[str, Any]:

        model_name = (
            type(
                self.model
            ).__name__
            if self.model is not None
            else None
        )

        tools = []

        if self.tools is not None:

            try:

                if hasattr(
                    self.tools,
                    "available",
                ):

                    tools = list(
                        self.tools.available()
                    )

            except Exception:

                tools = []

        return {
            "model": model_name,
            "memory": (
                type(
                    self.memory
                ).__name__
                if self.memory is not None
                else None
            ),
            "tools": tools,
            "active_conversation": (
                self.get_active_conversation_id()
            ),
            "history_messages": len(
                self.conversation_history
            ),
        }
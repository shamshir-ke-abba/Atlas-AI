"""Atlas V3 Brain

Central AI orchestration layer.

Responsibilities:
- Build conversation-aware prompts
- Maintain conversation history
- Handle deterministic conversation recall
- Route messages through ToolManager
- Execute deterministic tools
- Generate normal responses through AtlasModel
- Maintain compatibility with Controller and AIWorker
"""

from typing import Any, Dict, Optional

from core.logger import logger
from ai.model import AtlasModel
from ai.context_builder import ContextBuilder
from agents.coding.agent import CodingAgent
from agents.coding.detector import CodingTaskDetector

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
 
        self.coding_detector = CodingTaskDetector()
        self.coding_agent = CodingAgent()

        # Web-search state exposed to browser runtime.
        self.last_web_query = ""
        self.last_web_sources = []

        logger.info("AtlasBrain initialized")

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

    def set_active_conversation(self, conversation):
        self.active_conversation = conversation

        self.conversation_history = (
            self._extract_history(
                conversation
            )
        )

        logger.debug(
            "Active conversation updated: %d messages",
            len(self.conversation_history),
        )

    # --------------------------------------------------

    def set_conversation_history(self, history):
        if history is None:
            self.conversation_history = []
            return

        if isinstance(history, list):
            self.conversation_history = list(history)

            logger.debug(
                "Conversation history set: %d messages",
                len(self.conversation_history),
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

        conversation = self.active_conversation

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

            # Handle deterministic memory commands before routing
            # to the model. These include explicit "remember", "forget",
            # and simple recall queries such as "what is my name".
            if self.memory is not None:
                mem_cmd = self._handle_memory_command(
                    message
                )

                if mem_cmd is not None:
                    return mem_cmd

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

    def cancel_current(self) -> bool:
        """Cancel current model generation if active."""
        if self.model is not None and hasattr(self.model, "cancel_current"):
            return self.model.cancel_current()
        return False

    # ==================================================
    # WEB-FRIENDLY STREAMING
    # ==================================================

    def stream_message(
        self,
        message: str,
        conversation_history=None,
    ):

        """Yield response chunks for browser clients."""

        message = str(
            message or ""
        ).strip()

        if not message:
            yield "Error: Empty message"
            return

        if conversation_history is not None:
            self.set_conversation_history(
                conversation_history
            )

        # Deterministic memory commands handled synchronously
        if self.memory is not None:
            mem_cmd = self._handle_memory_command(
                message
            )

            if mem_cmd is not None:
                yield mem_cmd
                return

        try:

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

                yield recall_response
                return

            context = self._build_context(
                message
            )


            tool = None

            if (
                self.tools is not None
                and hasattr(
                    self.tools,
                    "match",
                )
            ):
                try:
                    tool = self.tools.match(
                        message
                    )

                except Exception as exc:

                    logger.warning(
                        "Web stream tool routing failed: %s",
                        exc,
                    )

            # ------------------------------------------
            # Tool response
            # ------------------------------------------

            if tool is not None:

                tool_name = str(
                    getattr(
                        tool,
                        "name",
                        "",
                    )
                ).lower()

                if tool_name == "web_search":

                    response = (
                        self._run_web_search_tool(
                            tool,
                            message,
                        )
                    )

                else:

                    response = (
                        self._run_tool(
                            tool,
                            message,
                        )
                    )

                self._update_memory(
                    message,
                    response,
                )

                yield response
                return

            # ------------------------------------------
            # Normal model response
            # ------------------------------------------

            prompt = (
                context.get(
                    "prompt",
                    "",
                )
                or
                self._fallback_prompt(
                    context.get(
                        "conversation_history",
                        [],
                    ),
                    message,
                )
            )

            parts = []

            for chunk in self.model.generate(
                prompt,
                stream=True,
            ):

                if chunk is None:
                    continue

                text = str(chunk)

                if text:

                    parts.append(
                        text
                    )

                    yield text

            response = "".join(
                parts
            ).strip()

            is_cancelled = getattr(self.model, "_cancelled", False)
            if not response and not is_cancelled:
                response = (
                    "No response generated."
                )
                yield response

            if not is_cancelled:
                self._update_memory(
                    message,
                    response,
                )

        except Exception as exc:

            logger.exception(
                "Brain streaming failed"
            )

            error = (
                f"Error: {exc}"
            )

            yield error

    # ==================================================
    # WEB SEARCH ANSWERING
    # ==================================================

    def _run_web_search_tool(
        self,
        tool,
        message: str,
    ) -> str:

        """Search web and answer using retrieved evidence."""

        try:

            query = message

            if hasattr(
                tool,
                "_clean_query",
            ):

                query = tool._clean_query(
                    message
                )

            self.last_web_query = str(
                query
            ).strip()

            results = []

            if hasattr(
                tool,
                "search_results",
            ):

                results = (
                    tool.search_results(
                        query
                    )
                )

            # ------------------------------------------
            # No structured results
            # ------------------------------------------

            if not results:

                raw = tool.run(
                    expression=message
                )

                self.last_web_sources = []

                return str(
                    raw
                ).strip()

            # ------------------------------------------
            # Save sources
            # ------------------------------------------

            self.last_web_sources = [
                {
                    "title": item.get(
                        "title",
                        "Source",
                    ),
                    "url": item.get(
                        "url",
                        "",
                    ),
                    "snippet": item.get(
                        "snippet",
                        "",
                    ),
                }

                for item in results

                if item.get(
                    "url"
                )
            ]

            # ------------------------------------------
            # Build evidence
            # ------------------------------------------

            evidence_lines = []

            for index, item in enumerate(
                results,
                1,
            ):

                evidence_lines.append(
                    f"[Source {index}] "
                    f"{item.get('title', 'Untitled')}\n"
                    f"URL: {item.get('url', '')}\n"
                    f"Snippet: {item.get('snippet', '')}"
                )

            prompt = (
                "You are Atlas, a helpful local AI assistant.\n\n"

                "Answer the user's CURRENT question "
                "using the web evidence below.\n"

                "Give the direct answer FIRST. "
                "Do not output a search-result list.\n"

                "Do not say you cannot browse. "
                "Do not invent facts that are not supported "
                "by the evidence.\n"

                "If the evidence is insufficient, "
                "say so clearly.\n"

                "Keep the answer concise unless "
                "the question needs explanation.\n\n"

                "CURRENT USER QUESTION:\n"
                f"{message}\n\n"

                "WEB EVIDENCE:\n"
                +
                "\n\n".join(
                    evidence_lines
                )
                +
                "\n\nANSWER:"
            )

            answer_parts = []

            for chunk in self.model.generate(
                prompt,
                stream=True,
            ):

                if chunk is not None:

                    answer_parts.append(
                        str(chunk)
                    )

            answer = "".join(
                answer_parts
            ).strip()

            if not answer:

                answer = (
                    "I found web results, "
                    "but could not generate "
                    "an answer from them."
                )

            source_lines = [
                "",
                "Sources",
            ]

            for item in self.last_web_sources[:6]:

                source_lines.append(
                    f"• {item['title']} — {item['url']}"
                )

            return (
                answer
                + "\n"
                + "\n".join(
                    source_lines
                )
            )

        except Exception as exc:

            logger.exception(
                "Web search answering failed"
            )

            return (
                f"Web search failed: {exc}"
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
                    memory=self._get_relevant_memory(current_message),
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

            tool_name = str(
                getattr(
                    tool,
                    "name",
                    type(tool).__name__,
                )
            ).lower()

            logger.info(
                "Executing tool: %s",
                tool_name,
            )

            # ==================================================
            # WEB SEARCH
            # ==================================================

            if tool_name == "web_search":

                return (
                    self._run_web_search_tool(
                        tool,
                        message,
                    )
                )

            # ==================================================
            # MATH
            # ==================================================

            if tool_name == "math":

                return (
                    self._run_math_tool(
                        tool,
                        message,
                    )
                )

            # ==================================================
            # FITNESS / NUTRITION
            # ==================================================
            #
            # IMPORTANT:
            #
            # FitnessPlugin and NutritionPlugin use:
            #
            #     run(action="", message="", **kwargs)
            #
            # Therefore the user's request MUST be passed
            # using the `message=` keyword.
            #
            # DO NOT do:
            #
            #     tool.run(message)
            #
            # because that makes the user's message become
            # `action`.
            #
            # ==================================================

            if tool_name in (
                "fitness",
                "nutrition",
            ):

                logger.info(
                    "Profile tool execution: "
                    "tool=%s message=%r",
                    tool_name,
                    message,
                )

                result = tool.run(
                    action="",
                    message=message,
                )

                if result is None:

                    return (
                        "No result returned by "
                        f"{tool_name} tool."
                    )

                return str(
                    result
                ).strip()

            # ==================================================
            # STANDARD TOOLS
            # ==================================================
            #
            # Prefer keyword arguments so plugins cannot
            # accidentally interpret the message as another
            # positional parameter.
            #
            # ==================================================

            try:

                result = tool.run(
                    message=message
                )

            except TypeError:

                try:

                    result = tool.run(
                        query=message
                    )

                except TypeError:

                    result = tool.run(
                        expression=message
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
    # MATH TOOL
    # ==================================================

    def _run_math_tool(
        self,
        tool,
        message: str,
    ) -> str:

        try:

            # --------------------------------------------------
            # Preferred new MathPlugin API
            # --------------------------------------------------

            operation = ""
            variable = "x"

            # ------------------------------------------
            # Detect operation
            # ------------------------------------------

            if hasattr(
                tool,
                "detect_operation",
            ):

                try:

                    operation = (
                        tool.detect_operation(
                            message
                        )
                    )

                except Exception as exc:

                    logger.warning(
                        "Math operation detection failed: %s",
                        exc,
                    )

            # ------------------------------------------
            # Detect variable
            # ------------------------------------------

            if hasattr(
                tool,
                "detect_variable",
            ):

                try:

                    variable = (
                        tool.detect_variable(
                            message,
                            message,
                        )
                    )

                except Exception as exc:

                    logger.warning(
                        "Math variable detection failed: %s",
                        exc,
                    )

            logger.info(
                "MATH REQUEST: operation=%s variable=%s",
                operation,
                variable,
            )

            # ------------------------------------------
            # Structured MathPlugin API
            # ------------------------------------------

            try:

                result = tool.run(
                    expression=message,
                    operation=operation,
                    variable=variable,
                )

                if result is not None:

                    return str(
                        result
                    ).strip()

            except TypeError as exc:

                logger.debug(
                    "Structured math execution unavailable: %s",
                    exc,
                )

            # ------------------------------------------
            # Legacy fallback
            # ------------------------------------------

            logger.debug(
                "Falling back to legacy math execution"
            )

            try:

                result = tool.run(
                    message
                )

            except TypeError:

                result = tool.run(
                    message=message
                )

            if result is None:

                return (
                    "No result returned by math tool."
                )

            return str(
                result
            ).strip()

        except Exception as exc:

            logger.exception(
                "Math tool execution failed"
            )

            return (
                f"Error executing math tool: {exc}"
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

            prompt = (
                self._fallback_prompt(
                    context.get(
                        "conversation_history",
                        [],
                    ),
                    message,
                )
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
    def _get_relevant_memory(
        self,
        current_message: str = "",
    ) -> Dict[str, Any]:
        """Retrieve only persistent memory relevant to the
        current user message.
        """

        if self.memory is None:
            return {}

        try:
            relevant = getattr(self.memory, "relevant", None)

            if callable(relevant):
                result = relevant(current_message)

                if isinstance(result, dict):
                    return result

        except Exception as exc:
            logger.warning(
                "Relevant memory retrieval failed: %s",
                exc,
            )

        return {}

    # ==================================================
    # MEMORY COMMAND HANDLING
    # ==================================================

    def _handle_memory_command(self, message: str) -> Optional[str]:
        """Detect and execute deterministic memory commands.

        Returns a string response if the message was a memory
        command and was handled here; otherwise returns None.
        """

        if self.memory is None:
            return None

        text = str(message or "").strip()
        lower = text.lower()

        # --------------------------------------------------
        # FORGET commands
        # --------------------------------------------------
        if lower.startswith("forget") or "forget that" in lower:
            # Basic patterns: "forget my name", "forget that my project is Atlas"
            try:
                # If MemoryManager offers a convenient `forget` API
                # we will try common mappings first.
                data = self.memory.all()

                # Attempt simple keyword mapping
                if "name" in lower:
                    self.memory.forget("identity", "name")
                    return "I've forgotten your name."

                if "favorite" in lower or "favourite" in lower or "color" in lower:
                    self.memory.forget("preferences", "favorite_color")
                    return "I've forgotten your favorite color."

                # Fallback: search facts for the mentioned phrase and remove matches
                facts = data.get("facts", {}) if isinstance(data, dict) else {}

                for k, v in list(facts.items()):
                    if isinstance(v, str) and v.lower() in lower:
                        self.memory.forget("facts", k)
                        return "I've forgotten that." 

                return "I couldn't find a matching saved memory to forget."

            except Exception as exc:
                logger.exception("Memory forget failed")
                return "Error: could not forget memory."

        # --------------------------------------------------
        # REMEMBER commands
        # --------------------------------------------------
        if lower.startswith("remember") or "remember that" in lower or lower.startswith("my name is"):
            try:
                # Prefer canonical extractor on MemoryManager
                extractor = getattr(self.memory, "extract_from_message", None)

                if callable(extractor):
                    extractor(text)

                    # Verify extraction via `relevant` if available
                    relevant = getattr(self.memory, "relevant", None)

                    if callable(relevant):
                        rel = relevant(text)

                        if rel:
                            # Build confirmation
                            parts = []

                            if "identity" in rel:
                                name = rel["identity"].get("name")
                                if name:
                                    parts.append(f"your name is {name}")

                            if "preferences" in rel:
                                for k, v in rel["preferences"].items():
                                    parts.append(f"your {k.replace('_',' ')} is {v}")

                            if "facts" in rel:
                                parts.append("some facts saved.")

                            if parts:
                                return (
                                    "Okay — I've saved that: "
                                    + "; ".join(parts)
                                )

                    # If extractor didn't produce relevant, still confirm generic save
                    return "Okay — I've saved that." 

                # Fallback: naive parsing for patterns like "my name is X"
                m = None

                if "my name is" in lower:
                    try:
                        name = text.split("my name is", 1)[1].strip().split()[0]
                        self.memory.remember("identity", "name", name)
                        return f"I'll remember that your name is {name}."
                    except Exception:
                        pass

                return None

            except Exception:
                logger.exception("Memory remember failed")
                return "Error: could not save memory."

        # --------------------------------------------------
        # RECALL queries — use MemoryManager.relevant for deterministic replies
        # --------------------------------------------------
        recall_triggers = (
            "what is my name",
            "what is my favourite",
            "what is my favorite",
            "what do you remember",
            "do you remember",
            "who am i",
            "what project",
            "what are my goals",
            "what kind of explanations do i prefer",
            "what operating system do i use",
            "what programming language is my project written in",
            "what language is my project written in",
            "what technology is my project using",
            "what is my project called",
            "what do you know about my project",
            "tell me about my project",
            "what is my project",
            "where do i live",
            "where do i stay",
            "where do i reside",
            "where am i based",
            "where am i living",
            "where am i staying",
            "what city do i live in",
            "which city do i live in",
            "what city i live in",
            "what is my city",
            "where do i work",
            "what is my workplace",
            "what is my job",
            "what is my role",
            "what do you know about me",
            "tell me what you know",
            "list my memories",
            "show memories",
        )

        if any(phrase in lower for phrase in recall_triggers):
            try:
                relevant = getattr(self.memory, "relevant", None)

                is_name_query = any(
                    p in lower
                    for p in (
                        "my name",
                        "who am i",
                        "what is my name",
                        "do you remember my name",
                        "naam",
                    )
                )
                is_location_query = any(
                    p in lower
                    for p in (
                        "where do i live",
                        "where i live",
                        "where do i stay",
                        "where i stay",
                        "where do i reside",
                        "where am i based",
                        "where am i living",
                        "what city",
                        "which city",
                        "my city",
                        "my location",
                        "where am i",
                        "kahan",
                        "rehta",
                    )
                )
                is_pref_query = any(
                    p in lower
                    for p in (
                        "favorite",
                        "favourite",
                        "prefer",
                        "preference",
                        "like",
                        "food",
                        "color",
                        "colour",
                        "explanations",
                        "explanation",
                        "answers",
                        "style",
                    )
                )
                is_project_query = any(
                    p in lower
                    for p in (
                        "project",
                        "app",
                        "application",
                        "software",
                        "code",
                        "technology",
                        "language",
                        "atlas",
                    )
                )
                is_environment_query = any(
                    p in lower
                    for p in (
                        "os",
                        "operating system",
                        "ubuntu",
                        "windows",
                        "linux",
                        "macos",
                        "what system",
                        "do i use",
                    )
                )
                is_broad_query = any(
                    p in lower
                    for p in (
                        "what do you remember",
                        "what do you know about me",
                        "tell me what you know",
                        "everything you remember",
                        "list my memories",
                        "show memories",
                        "all memories",
                        "what is in your memory",
                    )
                )
                is_fact_query = any(
                    p in lower
                    for p in (
                        "facts",
                        "what did i tell you",
                        "what did i say",
                        "saved facts",
                    )
                )

                if callable(relevant):
                    rel = relevant(text)

                    # Broad memory summary across multiple categories
                    if is_broad_query and rel:
                        parts = []
                        if "identity" in rel and isinstance(rel["identity"], dict):
                            ident = rel["identity"]
                            if "name" in ident:
                                parts.append(f"your name is {ident['name']}")
                            if "city" in ident:
                                parts.append(f"you live in {ident['city']}")
                            if "workplace" in ident:
                                parts.append(f"you work at {ident['workplace']}")
                            if "role" in ident:
                                parts.append(f"your role is {ident['role']}")

                        if "preferences" in rel and isinstance(rel["preferences"], dict):
                            for k, v in rel["preferences"].items():
                                if v:
                                    tag = k.replace("favorite_", "")
                                    parts.append(f"your favorite {tag} is {v}" if k.startswith("favorite_") else f"you prefer {k.replace('_', ' ')}: {v}")

                        if "environment" in rel and isinstance(rel["environment"], dict):
                            if "operating_system" in rel["environment"]:
                                parts.append(f"you use {rel['environment']['operating_system']}")

                        if "projects" in rel and isinstance(rel["projects"], dict):
                            if "project_name" in rel["projects"]:
                                parts.append(f"your project is {rel['projects']['project_name']}")

                        if "facts" in rel:
                            facts_data = rel["facts"]
                            fvals = [str(v).strip() for v in (facts_data.values() if isinstance(facts_data, dict) else facts_data) if v]
                            if fvals:
                                parts.append("saved facts: " + "; ".join(fvals[:3]))

                        if parts:
                            return "Here is what I remember: " + "; ".join(parts) + "."

                    if is_name_query and rel.get("identity"):
                        name = rel["identity"].get("name")
                        if name:
                            return f"Your name is {name}."

                    if (is_location_query or any(w in lower for w in ("live", "city", "stay", "reside", "location", "based", "where"))) and rel.get("identity"):
                        city = rel["identity"].get("city")
                        if city:
                            return f"You live in {city}."

                    if any(w in lower for w in ("work", "job", "company", "employer", "office", "working")) and rel.get("identity"):
                        workplace = rel["identity"].get("workplace")
                        if workplace:
                            return f"You work at {workplace}."
                        role = rel["identity"].get("role")
                        if role:
                            return f"Your role is {role}."

                    if is_pref_query and rel.get("preferences"):
                        prefs = rel["preferences"]
                        if "explanation_style" in prefs and any(w in lower for w in ("explanation", "explain", "style", "answer")):
                            return f"You prefer explanations {prefs['explanation_style']}."
                        if "favorite_color" in prefs and any(w in lower for w in ("color", "colour", "rang")):
                            return f"Your favorite color is {prefs['favorite_color']}."
                        if "favorite_food" in prefs and any(w in lower for w in ("food", "eat", "dish", "khana")):
                            return f"Your favorite food is {prefs['favorite_food']}."
                        for key, value in prefs.items():
                            if value:
                                tag = key.replace("favorite_", "")
                                return f"Your favorite {tag} is {value}." if key.startswith("favorite_") else f"You prefer {key.replace('_', ' ')}: {value}."

                    if is_project_query and rel.get("projects"):
                        proj = rel["projects"]
                        if "project_name" in proj and proj["project_name"]:
                            return f"Your project is called {proj['project_name']}."
                        if "technology" in proj and proj["technology"]:
                            return f"Your project is written in {proj['technology']}."
                        if "runtime" in proj and proj["runtime"]:
                            return f"Your project uses {proj['runtime']}."

                    if is_environment_query and rel.get("environment"):
                        env = rel["environment"]
                        if "operating_system" in env:
                            return f"You use {env['operating_system']}."

                    if is_fact_query and rel.get("facts"):
                        facts = rel["facts"]
                        if isinstance(facts, dict):
                            values = [str(v).strip() for v in facts.values() if v]
                        elif isinstance(facts, list):
                            values = [str(v).strip() for v in facts if v]
                        else:
                            values = []
                        if values:
                            return (
                                "I have the following facts saved: "
                                + "; ".join(values[:5])
                            )

                # Category-specific fallbacks
                if is_name_query:
                    try:
                        name = self.memory.recall("identity", "name")
                        if name:
                            return f"Your name is {name}."
                    except Exception:
                        pass

                if is_location_query:
                    try:
                        city = self.memory.recall("identity", "city")
                        if city:
                            return f"You live in {city}."
                    except Exception:
                        pass

                if is_pref_query:
                    try:
                        val = self.memory.recall("preferences", "explanation_style")
                        if val:
                            return f"You prefer explanations {val}."
                        val = self.memory.recall("preferences", "favorite_color")
                        if val and any(w in lower for w in ("color", "colour")):
                            return f"Your favorite color is {val}."
                        val = self.memory.recall("preferences", "favorite_food")
                        if val and any(w in lower for w in ("food", "eat")):
                            return f"Your favorite food is {val}."
                    except Exception:
                        pass

                if is_project_query:
                    try:
                        project_name = self.memory.recall("projects", "project_name")
                        if project_name:
                            return f"Your project is called {project_name}."
                        technology = self.memory.recall("projects", "technology")
                        if technology:
                            return f"Your project is written in {technology}."
                        runtime = self.memory.recall("projects", "runtime")
                        if runtime:
                            return f"Your project uses {runtime}."
                    except Exception:
                        pass

                if is_environment_query:
                    try:
                        val = self.memory.recall("environment", "operating_system")
                        if val:
                            return f"You use {val}."
                    except Exception:
                        pass

                if is_fact_query:
                    try:
                        all_mem = self.memory.all() if hasattr(self.memory, "all") else {}
                        facts = all_mem.get("facts", {}) if isinstance(all_mem, dict) else {}
                        if isinstance(facts, dict):
                            values = [str(v).strip() for v in facts.values() if v]
                        elif isinstance(facts, list):
                            values = [str(v).strip() for v in facts if v]
                        else:
                            values = []
                        if values:
                            return (
                                "I have the following facts saved: "
                                + "; ".join(values[:5])
                            )
                    except Exception:
                        pass

                # Nothing found for the specific query
                return "I don't have that saved."

            except Exception:
                logger.exception("Memory recall failed")
                return None

        return None
    
    # --------------------------------------------------

    def _update_memory(
        self,
        message: str,
        response: str,
    ):

        if self.memory is None:
            return

        try:

            # Preferred: if the memory implementation offers
            # an extractor that can parse user messages into
            # structured facts, use it. This avoids misusing
            # the low-level `remember` API.
            if hasattr(self.memory, "extract_from_message"):
                try:
                    # Extract facts from the user's message.
                    self.memory.extract_from_message(
                        message
                    )

                except Exception:
                    # Fall through to other methods on failure.
                    pass

                return

            # Do NOT persist model responses automatically. Only extract
            # persistent facts from user messages via `extract_from_message`.
            # This prevents hallucinated model outputs from becoming memory.
            return

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

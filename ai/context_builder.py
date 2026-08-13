"""
Atlas V3 Context Builder

Builds the complete prompt sent to AtlasModel.

Responsibilities:
- Include system instructions
- Include conversation history
- Clearly distinguish User and Atlas
- Include current user message
- Keep recent history within MAX_HISTORY
"""

from typing import Any, Dict, List

from config import MAX_HISTORY


class ContextBuilder:
    """Build conversation-aware prompts for Atlas."""

    def __init__(self):
        self.max_history = MAX_HISTORY

    # ==================================================
    # MAIN BUILDER
    # ==================================================

    def build(
        self,
        conversation_history: List[Dict[str, Any]],
        current_message: str,
    ) -> str:

        current_message = str(
            current_message or ""
        ).strip()

        history = (
            conversation_history
            if isinstance(
                conversation_history,
                list,
            )
            else []
        )

        # --------------------------------------------------
        # System instructions
        # --------------------------------------------------

        system_prompt = """
You are Atlas, a local AI assistant.

IMPORTANT CONVERSATION RULES:

1. You have access to the conversation history below.
2. Treat the history as the actual conversation between you and the user.
3. Remember information stated earlier in THIS conversation.
4. If the user asks "what did I just tell you?", answer using the immediately preceding user message.
5. Do NOT claim that you cannot remember previous messages when they are present in the conversation history.
6. Do NOT mention a knowledge cutoff when answering questions about this conversation.
7. Do NOT pretend that you are unable to access the conversation history.
8. Answer naturally and directly.
9. Do not repeat the entire conversation unless the user asks for it.
"""

        prompt = (
            system_prompt.strip()
            + "\n\n"
        )

        # --------------------------------------------------
        # Conversation history
        # --------------------------------------------------

        prompt += (
            "===== CONVERSATION HISTORY =====\n"
        )

        # Only include recent messages.
        recent_history = history[
            -self.max_history:
        ]

        if recent_history:

            for msg in recent_history:

                if not isinstance(
                    msg,
                    dict,
                ):
                    continue

                sender = str(
                    msg.get(
                        "sender",
                        "",
                    )
                ).strip()

                text = str(
                    msg.get(
                        "text",
                        "",
                    )
                ).strip()

                if not text:
                    continue

                # --------------------------------------------------
                # Normalize sender
                # --------------------------------------------------

                if (
                    sender.lower()
                    in (
                        "you",
                        "user",
                    )
                ):

                    prompt += (
                        f"User: {text}\n"
                    )

                elif (
                    sender.lower()
                    in (
                        "atlas",
                        "assistant",
                        "ai",
                    )
                ):

                    prompt += (
                        f"Atlas: {text}\n"
                    )

                else:

                    prompt += (
                        f"{sender or 'User'}: "
                        f"{text}\n"
                    )

        else:

            prompt += (
                "(No previous messages.)\n"
            )

        prompt += (
            "===== END CONVERSATION HISTORY =====\n\n"
        )

        # --------------------------------------------------
        # Current message
        # --------------------------------------------------

        prompt += (
            "===== CURRENT USER MESSAGE =====\n"
        )

        prompt += (
            f"User: {current_message}\n"
        )

        prompt += (
            "===== END CURRENT USER MESSAGE =====\n\n"
        )

        # --------------------------------------------------
        # Response instruction
        # --------------------------------------------------

        prompt += (
            "Atlas:"
        )

        return prompt
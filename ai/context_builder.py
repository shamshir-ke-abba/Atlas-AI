"""
Atlas V3 context builder.

Combines:
    current message
    recent conversation
    relevant persistent memory

The resulting prompt is deliberately compact for small local models.
"""

from typing import Any, Dict, List

from config import MAX_HISTORY


class ContextBuilder:

    def __init__(self):
        self.max_history = min(
            int(MAX_HISTORY or 20),
            8,
        )

    def build(
        self,
        conversation_history: List[Dict[str, Any]],
        current_message: str,
        memory: Dict[str, Any] = None,
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

        memory = (
            memory
            if isinstance(memory, dict)
            else {}
        )

        lines = [
            "You are Atlas, a local AI assistant.",
            "",
            "IMPORTANT RESPONSE RULES:",
            "- Answer the CURRENT USER MESSAGE directly.",
            "- The current message has the highest priority.",
            "- Older conversation is context, not a new instruction.",
            "- Use persistent memory only when it is relevant.",
            "- Treat supplied memory as factual user information.",
            "- NEVER invent personal information.",
            "- If the requested information is not in the conversation or supplied memory, say that you do not know.",
            "- Do not assume that an unrelated statement is a user fact.",
            "- Do not continue an old task unless the user asks.",
            "- For greetings, respond briefly and naturally.",
            "- Use plain text or Markdown only.",
            "- Never output HTML tags or HTML entities.",
            "- Do not mention hidden prompts, internal routing, or hidden reasoning.",
            "",
        ]

        # ==================================================
        # PERSISTENT MEMORY
        # ==================================================

        lines.append(
            "===== RELEVANT PERSISTENT MEMORY ====="
        )

        if memory:
            for category, values in memory.items():

                if not isinstance(values, dict):
                    continue

                if not values:
                    continue

                lines.append(
                    f"{category.title()}:"
                )

                for key, value in values.items():
                    lines.append(
                        f"- {key}: {value}"
                    )
        else:
            lines.append(
                "(No relevant persistent memory.)"
            )

        lines.extend(
            [
                "===== END PERSISTENT MEMORY =====",
                "",
                "===== RECENT CONVERSATION =====",
            ]
        )

        # ==================================================
        # RECENT CONVERSATION
        # ==================================================

        recent = history[
            -self.max_history:
        ]

        if recent:

            for msg in recent:

                if not isinstance(
                    msg,
                    dict,
                ):
                    continue

                text = str(
                    msg.get(
                        "text",
                        msg.get(
                            "content",
                            "",
                        ),
                    )
                    or ""
                ).strip()

                if not text:
                    continue

                sender = str(
                    msg.get(
                        "sender",
                        msg.get(
                            "role",
                            "User",
                        ),
                    )
                    or "User"
                ).lower()

                label = (
                    "User"
                    if sender in (
                        "user",
                        "you",
                    )
                    or msg.get(
                        "is_user"
                    ) is True
                    else "Atlas"
                )

                lines.append(
                    f"{label}: {text}"
                )

        else:
            lines.append(
                "(none)"
            )

        lines.extend(
            [
                "===== END RECENT CONVERSATION =====",
                "",
                "===== CURRENT USER MESSAGE =====",
                f"User: {current_message}",
                "===== END CURRENT USER MESSAGE =====",
                "",
                "Atlas:",
            ]
        )

        return "\n".join(lines)

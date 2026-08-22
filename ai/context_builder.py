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

        # If the current message is a short follow-up, attempt to
        # resolve its reference to the most recent assistant message
        # or to a specific enumerated item. This helps the model
        # correctly interpret pronouns like "that", "the second one",
        # or short clarifications.
        clarification = self._resolve_followup(recent, current_message)

        lines.extend(
            [
                "===== END RECENT CONVERSATION =====",
                "",
            ]
        )

        if clarification:
            lines.append("===== FOLLOW-UP CLARIFICATION =====")
            lines.append(clarification)
            lines.append("===== END FOLLOW-UP CLARIFICATION =====")
            lines.append("")

        lines.extend(
            [
                "===== CURRENT USER MESSAGE =====",
                f"User: {current_message}",
                "===== END CURRENT USER MESSAGE =====",
                "",
                "Atlas:",
            ]
        )

        return "\n".join(lines)

    def _resolve_followup(self, recent: List[Dict[str, Any]], current_message: str) -> str:
        """
        If the current message is a short follow-up referring to recent
        assistant output, return a short clarifying note that will be
        injected into the prompt to disambiguate references for the model.
        Returns empty string when no clarification is needed.
        """

        if not current_message:
            return ""

        # Heuristic: only short follow-ups are auto-resolved
        token_count = len(current_message.split())
        if token_count > 10:
            return ""

        text = current_message.lower()

        followup_signals = (
            "that",
            "it",
            "the second",
            "second",
            "the first",
            "first",
            "the third",
            "third",
            "the other",
            "other",
            "that one",
            "explain that",
            "explain this",
            "explain the",
            "what about",
            "why",
            "how",
            "tell me more",
            "another one",
            "the second one",
            "the first one",
            "the third one",
        )

        # Match signals as whole words/phrases to avoid matching
        # substrings inside unrelated words (e.g. "it" in "capital").
        import re as _re

        pattern = r"\b(?:" + "|".join(_re.escape(s) for s in followup_signals) + r")\b"
        if not _re.search(pattern, text, _re.IGNORECASE):
            return ""

        # Find last assistant message text
        assistant_text = None
        for msg in reversed(recent or []):
            if not isinstance(msg, dict):
                continue
            is_user = msg.get("is_user")
            sender = str(msg.get("sender", msg.get("role", "User")) or "").lower()
            if (is_user is True) or sender in ("user", "you"):
                continue
            # This is an assistant message
            assistant_text = str(msg.get("text") or msg.get("content") or "").strip()
            if assistant_text:
                break

        if not assistant_text:
            return ""

        # If the assistant text contains numbered items, try to extract
        # the referenced item for more precise disambiguation.
        # items extraction uses regex too
        items = []
        import re as _re
        for line in assistant_text.splitlines():
            m = _re.match(r"^\s*(?:\d+|[ivx]+)[\.)]\s*(.+)", line.strip(), _re.IGNORECASE)
            if m:
                items.append(m.group(1).strip())

        ordinal_map = {"first": 1, "second": 2, "third": 3}

        for word, idx in ordinal_map.items():
            if word in text and items and len(items) >= idx:
                return f"User's short follow-up appears to refer to the assistant's enumerated item #{idx}: \"{items[idx-1]}\""

        # If no numbered resolution, include a short quote of the assistant message
        short = assistant_text
        if len(short) > 240:
            short = short[:240].rsplit(" ", 1)[0] + "..."

        return f"User's short follow-up appears to refer to the most recent assistant message: \"{short}\""

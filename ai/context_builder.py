"""
Atlas V3 context builder.

Combines:
    authoritative system prompt
    relevant persistent memory
    recent conversation
    current message

The resulting prompt is structured, compact, and deterministic.
"""

from typing import Any, Dict, List, Optional
import re as _re

from config import MAX_HISTORY
from ai.prompts import SYSTEM_PROMPT


class ContextBuilder:

    def __init__(self, max_history: Optional[int] = None):
        if max_history is not None:
            self.max_history = max(1, int(max_history))
        else:
            self.max_history = max(1, int(MAX_HISTORY or 20))

    def build(
        self,
        conversation_history: List[Dict[str, Any]],
        current_message: str,
        memory: Optional[Dict[str, Any]] = None,
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
            SYSTEM_PROMPT,
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
                if not values:
                    continue

                if isinstance(values, dict):
                    lines.append(f"{category.title()}:")
                    for key, value in values.items():
                        lines.append(f"- {key}: {value}")
                elif isinstance(values, list):
                    lines.append(f"{category.title()}:")
                    for item in values:
                        lines.append(f"- {item}")
                elif isinstance(values, str):
                    lines.append(f"- {category}: {values}")
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
        ] if self.max_history > 0 else []

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

        # Clarify short follow-up pronouns when referencing assistant output
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

        token_count = len(current_message.split())
        if token_count > 15:
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
        items = []
        for line in assistant_text.splitlines():
            m = _re.match(r"^\s*(?:\d+|[ivx]+)[\.)]\s*(.+)", line.strip(), _re.IGNORECASE)
            if m:
                items.append(m.group(1).strip())

        ordinal_map = {"first": 1, "second": 2, "third": 3}

        for word, idx in ordinal_map.items():
            if word in text and items and len(items) >= idx:
                return f"User's short follow-up appears to refer to the assistant's enumerated item #{idx}: \"{items[idx-1]}\""

        # If the assistant text was a simple question and user statement doesn't have explicit explain signals,
        # avoid misattributing user subject statements to assistant's question.
        if assistant_text.strip().endswith("?") and not any(w in text for w in ("why", "how", "what about", "explain", "that", "tell me more")):
            return ""

        short = assistant_text
        if len(short) > 240:
            short = short[:240].rsplit(" ", 1)[0] + "..."

        return f"User's short follow-up appears to refer to the most recent assistant message: \"{short}\""

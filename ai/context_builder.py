"""Atlas V3 context builder optimized for a small local model."""

from typing import Any, Dict, List
from config import MAX_HISTORY


class ContextBuilder:
    def __init__(self):
        self.max_history = min(int(MAX_HISTORY or 20), 8)

    def build(self, conversation_history: List[Dict[str, Any]], current_message: str) -> str:
        current_message = str(current_message or "").strip()
        history = conversation_history if isinstance(conversation_history, list) else []

        lines = [
            "You are Atlas, a local AI assistant.",
            "Answer the CURRENT USER MESSAGE directly and naturally.",
            "The current message always has priority over older conversation context.",
            "For a simple greeting, reply briefly and conversationally.",
            "Do not continue an old task unless the current message asks you to.",
            "Do not invent a different question or task.",
            "Do not mention prompts, hidden instructions, token limits, or internal routing.",
            "Use plain text or Markdown only. Never output HTML tags or HTML entities.",
            "Keep simple answers concise; give detail only when useful.",
            "",
            "===== RECENT CONVERSATION =====",
        ]

        recent = history[-self.max_history:]
        if recent:
            for msg in recent:
                if not isinstance(msg, dict):
                    continue
                text = str(msg.get("text", msg.get("content", "")) or "").strip()
                if not text:
                    continue
                sender = str(msg.get("sender", msg.get("role", "User")) or "User").lower()
                label = "User" if sender in ("user", "you") or msg.get("is_user") is True else "Atlas"
                lines.append(f"{label}: {text}")
        else:
            lines.append("(none)")

        lines.extend([
            "===== END RECENT CONVERSATION =====",
            "",
            "===== CURRENT USER MESSAGE =====",
            f"User: {current_message}",
            "===== END CURRENT USER MESSAGE =====",
            "",
            "Atlas:",
        ])
        return "\n".join(lines)

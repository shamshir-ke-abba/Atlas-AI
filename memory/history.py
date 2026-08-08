"""
Atlas V3 Conversation Manager

Maintains the active conversation independently
from the LLM implementation.
"""

from config import MAX_HISTORY


class ConversationManager:

    def __init__(self):
        self.messages = []

    # --------------------------------------------------
    # Add Messages
    # --------------------------------------------------

    def add_user(self, text):
        self.messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

        self._trim()

    def add_assistant(self, text):
        self.messages.append(
            {
                "role": "assistant",
                "content": text,
            }
        )

        self._trim()

    # --------------------------------------------------
    # Retrieval
    # --------------------------------------------------

    def history(self):
        return self.messages.copy()

    def last(self, amount=None):
        if amount is None:
            amount = MAX_HISTORY

        return self.messages[-amount:]

    # --------------------------------------------------
    # Maintenance
    # --------------------------------------------------

    def clear(self):
        self.messages.clear()

    # --------------------------------------------------
    # Internal
    # --------------------------------------------------

    def _trim(self):
        if len(self.messages) > MAX_HISTORY:
            self.messages = self.messages[-MAX_HISTORY:]
"""
Atlas V3 Conversation Manager

Manages the active conversation independently
from the LLM implementation.
"""

from datetime import datetime
from uuid import uuid4

from config import MAX_HISTORY


class ConversationManager:

    def __init__(self):

        self.conversation_id = self._new_id()
        self.title = "New Chat"
        self.created_at = self._timestamp()
        self.updated_at = self.created_at

        self.messages = []

    # ==================================================
    # Conversation Identity
    # ==================================================

    @staticmethod
    def _new_id():

        return str(
            uuid4()
        )

    @staticmethod
    def _timestamp():

        return datetime.now().isoformat(
            timespec="seconds"
        )

    # ==================================================
    # Add Messages
    # ==================================================

    def add_user(
        self,
        text,
    ):

        self.messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

        self._update()

        self._trim()

    def add_assistant(
        self,
        text,
    ):

        self.messages.append(
            {
                "role": "assistant",
                "content": text,
            }
        )

        self._update()

        self._trim()

    # ==================================================
    # Retrieval
    # ==================================================

    def history(self):

        return self.messages.copy()

    def last(
        self,
        amount=None,
    ):

        if amount is None:
            amount = MAX_HISTORY

        return self.messages[-amount:]

    # ==================================================
    # Conversation Information
    # ==================================================

    def get_id(self):

        return self.conversation_id

    def get_title(self):

        return self.title

    def get_created_at(self):

        return self.created_at

    def get_updated_at(self):

        return self.updated_at

    # ==================================================
    # Title
    # ==================================================

    def set_title(
        self,
        title,
    ):

        title = title.strip()

        if not title:
            return

        self.title = title

        self._update()

    # ==================================================
    # Clear
    # ==================================================

    def clear(self):

        self.messages.clear()

        self.title = "New Chat"

        self._update()

    # ==================================================
    # New Conversation
    # ==================================================

    def new_conversation(self):

        self.conversation_id = self._new_id()

        self.title = "New Chat"

        self.created_at = self._timestamp()

        self.updated_at = self.created_at

        self.messages.clear()

    # ==================================================
    # Serialization
    # ==================================================

    def to_dict(self):

        return {
            "id": self.conversation_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": self.messages.copy(),
        }

    # ==================================================
    # Loading
    # ==================================================

    def load(
        self,
        data,
    ):

        self.conversation_id = data.get(
            "id",
            self._new_id(),
        )

        self.title = data.get(
            "title",
            "New Chat",
        )

        self.created_at = data.get(
            "created_at",
            self._timestamp(),
        )

        self.updated_at = data.get(
            "updated_at",
            self.created_at,
        )

        self.messages = data.get(
            "messages",
            [],
        ).copy()

        self._trim()

    # ==================================================
    # Internal
    # ==================================================

    def _update(self):

        self.updated_at = self._timestamp()

    def _trim(self):

        if len(self.messages) > MAX_HISTORY:

            self.messages = self.messages[
                -MAX_HISTORY:
            ]
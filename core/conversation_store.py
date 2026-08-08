"""
Atlas V3 Conversation Store

Handles persistent storage of conversations.
The GUI and AI should not need to know
how conversations are stored on disk.
"""

import json
from pathlib import Path


class ConversationStore:

    def __init__(self):

        self.directory = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "conversations"
        )

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ==================================================
    # Save
    # ==================================================

    def save(
        self,
        conversation,
    ):

        data = conversation.to_dict()

        path = self.directory / (
            f"{conversation.get_id()}.json"
        )

        temporary = path.with_suffix(
            ".tmp"
        )

        with open(
            temporary,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False,
            )

        temporary.replace(
            path
        )

    # ==================================================
    # Load
    # ==================================================

    def load(
        self,
        conversation_id,
    ):

        path = self.directory / (
            f"{conversation_id}.json"
        )

        if not path.exists():
            return None

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(
                file
            )

    # ==================================================
    # List Conversations
    # ==================================================

    def list_conversations(self):

        conversations = []

        for path in self.directory.glob(
            "*.json"
        ):

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8",
                ) as file:

                    data = json.load(
                        file
                    )

                conversations.append(
                    {
                        "id": data.get(
                            "id"
                        ),
                        "title": data.get(
                            "title",
                            "New Chat",
                        ),
                        "created_at": data.get(
                            "created_at",
                            "",
                        ),
                        "updated_at": data.get(
                            "updated_at",
                            "",
                        ),
                    }
                )

            except (
                json.JSONDecodeError,
                OSError,
            ):

                continue

        conversations.sort(
            key=lambda item: item.get(
                "updated_at",
                "",
            ),
            reverse=True,
        )

        return conversations

    # ==================================================
    # Delete
    # ==================================================

    def delete(
        self,
        conversation_id,
    ):

        path = self.directory / (
            f"{conversation_id}.json"
        )

        if path.exists():

            path.unlink()

            return True

        return False

    # ==================================================
    # Exists
    # ==================================================

    def exists(
        self,
        conversation_id,
    ):

        path = self.directory / (
            f"{conversation_id}.json"
        )

        return path.exists()

    # ==================================================
    # Clear All
    # ==================================================

    def clear_all(self):

        for path in self.directory.glob(
            "*.json"
        ):

            try:

                path.unlink()

            except OSError:

                pass
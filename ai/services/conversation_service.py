"""
Atlas V3 Conversation Service

Persistent conversation management.
"""

import json
import logging
import uuid

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import CONVERSATIONS_DIR


logger = logging.getLogger(__name__)


class ConversationService:
    """
    Manages Atlas conversations.

    The service represents the currently loaded
    conversation.

    Sidebar operations use list(), which returns
    dictionaries.

    Chat/Brain operations use history().
    """

    def __init__(self):

        self.conversations_dir = Path(
            CONVERSATIONS_DIR
        )

        self.conversations_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.current_id: Optional[str] = None

        self.current_messages: List[
            Dict[str, Any]
        ] = []

        self.current_title = "New Chat"

    # ==================================================
    # CREATE
    # ==================================================

    def new(self) -> str:

        conversation_id = str(
            uuid.uuid4()
        )

        self.current_id = conversation_id

        self.current_messages = []

        self.current_title = "New Chat"

        self._save_current()

        logger.info(
            "Created conversation: %s",
            conversation_id,
        )

        return conversation_id

    # ==================================================
    # LOAD
    # ==================================================

    def load(
        self,
        conversation_id: str,
    ) -> bool:

        try:

            file_path = self._get_path(
                conversation_id
            )

            if not file_path.exists():

                logger.warning(
                    "Conversation not found: %s",
                    conversation_id,
                )

                return False

            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

            if not isinstance(
                data,
                dict,
            ):

                return False

            self.current_id = (
                conversation_id
            )

            messages = data.get(
                "messages",
                [],
            )

            if not isinstance(
                messages,
                list,
            ):

                messages = []

            self.current_messages = list(
                messages
            )

            self.current_title = str(
                data.get(
                    "title",
                    self._get_title(),
                )
            )

            logger.info(
                "Loaded conversation: %s",
                conversation_id,
            )

            return True

        except Exception as exc:

            logger.exception(
                "Error loading conversation: %s",
                exc,
            )

            return False

    # ==================================================
    # CURRENT CONVERSATION
    # ==================================================

    def get_id(self) -> Optional[str]:

        return self.current_id

    # --------------------------------------------------

    def get(self):

        return self

    # --------------------------------------------------

    def history(self) -> List[Dict[str, Any]]:

        return list(
            self.current_messages
        )

    # --------------------------------------------------

    def last(self) -> List[Dict[str, Any]]:

        return self.history()

    # ==================================================
    # ADD USER MESSAGE
    # ==================================================

    def add_user(
        self,
        message: str,
    ) -> None:

        message = str(
            message
        ).strip()

        if not message:
            return

        self.current_messages.append(
            {
                "sender": "You",
                "role": "user",
                "text": message,
                "content": message,
                "is_user": True,
                "timestamp": datetime.now().isoformat(),
            }
        )

        if (
            self.current_title == "New Chat"
            or not self.current_title
        ):

            self.current_title = (
                self._generate_title(
                    message
                )
            )

    # ==================================================
    # ADD ASSISTANT MESSAGE
    # ==================================================

    def add_assistant(
        self,
        message: str,
    ) -> None:

        message = str(
            message
        ).strip()

        if not message:
            return

        self.current_messages.append(
            {
                "sender": "Atlas",
                "role": "assistant",
                "text": message,
                "content": message,
                "is_user": False,
                "timestamp": datetime.now().isoformat(),
            }
        )

    # ==================================================
    # SAVE
    # ==================================================

    def save(self) -> bool:

        return self._save_current()

    # --------------------------------------------------

    def _save_current(self) -> bool:

        try:

            if not self.current_id:

                return False

            file_path = self._get_path(
                self.current_id
            )

            created = None

            if file_path.exists():

                try:

                    with file_path.open(
                        "r",
                        encoding="utf-8",
                    ) as file:

                        old_data = json.load(
                            file
                        )

                    created = old_data.get(
                        "created"
                    )

                except Exception:

                    created = None

            data = {
                "id": self.current_id,
                "title": (
                    self.current_title
                    or self._get_title()
                ),
                "created": (
                    created
                    or datetime.now().isoformat()
                ),
                "messages": self.current_messages,
            }

            with file_path.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

            return True

        except Exception as exc:

            logger.exception(
                "Error saving conversation: %s",
                exc,
            )

            return False

    # ==================================================
    # TITLE
    # ==================================================

    def _generate_title(
        self,
        message: str,
    ) -> str:

        title = " ".join(
            str(message)
            .strip()
            .split()
        )

        if len(title) > 45:

            title = (
                title[:45].rstrip()
                + "..."
            )

        return title or "New Chat"

    # --------------------------------------------------

    def _get_title(self) -> str:

        if self.current_title:

            return self.current_title

        if not self.current_messages:

            return "New Chat"

        first = self.current_messages[0]

        if not isinstance(
            first,
            dict,
        ):

            return "New Chat"

        text = (
            first.get("text")
            or first.get("content")
            or ""
        )

        return self._generate_title(
            text
        )

    # --------------------------------------------------

    def auto_title(
        self,
        message: str,
    ) -> str:

        if (
            not self.current_title
            or self.current_title == "New Chat"
        ):

            self.current_title = (
                self._generate_title(
                    message
                )
            )

            self.save()

        return self.current_title

    # ==================================================
    # LIST
    # ==================================================

    def list(self) -> Dict[str, Dict]:

        conversations = {}

        try:

            files = sorted(
                self.conversations_dir.glob(
                    "*.json"
                ),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )

            for file_path in files:

                try:

                    with file_path.open(
                        "r",
                        encoding="utf-8",
                    ) as file:

                        data = json.load(
                            file
                        )

                    if not isinstance(
                        data,
                        dict,
                    ):

                        continue

                    conversation_id = str(
                        data.get(
                            "id",
                            file_path.stem,
                        )
                    )

                    messages = data.get(
                        "messages",
                        [],
                    )

                    if not isinstance(
                        messages,
                        list,
                    ):

                        messages = []

                    conversations[
                        conversation_id
                    ] = {
                        "id": conversation_id,
                        "title": data.get(
                            "title",
                            "New Chat",
                        ),
                        "created": data.get(
                            "created"
                        ),
                        "messages": messages,
                    }

                except Exception as exc:

                    logger.warning(
                        "Could not read %s: %s",
                        file_path,
                        exc,
                    )

        except Exception as exc:

            logger.exception(
                "Error listing conversations: %s",
                exc,
            )

        return conversations

    # ==================================================
    # GET SPECIFIC CONVERSATION
    # ==================================================

    def get_conversation(
        self,
        conversation_id: str,
    ):

        return self.list().get(
            conversation_id
        )

    # ==================================================
    # DELETE
    # ==================================================

    def delete(
        self,
        conversation_id: str,
    ) -> bool:

        try:

            file_path = self._get_path(
                conversation_id
            )

            if not file_path.exists():

                return False

            file_path.unlink()

            logger.info(
                "Deleted conversation: %s",
                conversation_id,
            )

            if (
                conversation_id
                == self.current_id
            ):

                self.current_id = None

                self.current_messages = []

                self.current_title = "New Chat"

            return True

        except Exception as exc:

            logger.exception(
                "Error deleting conversation: %s",
                exc,
            )

            return False

    # ==================================================
    # RENAME
    # ==================================================

    def rename(
        self,
        conversation_id: str,
        new_title: str,
    ) -> bool:

        try:

            new_title = str(
                new_title
            ).strip()

            if not new_title:

                return False

            file_path = self._get_path(
                conversation_id
            )

            if not file_path.exists():

                return False

            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

            data["title"] = new_title

            with file_path.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

            if (
                conversation_id
                == self.current_id
            ):

                self.current_title = new_title

            return True

        except Exception as exc:

            logger.exception(
                "Error renaming conversation: %s",
                exc,
            )

            return False

    # ==================================================
    # CLEAR
    # ==================================================

    def clear(self) -> None:

        self.current_messages = []

        self.current_title = "New Chat"

        self._save_current()

    # ==================================================
    # PATH
    # ==================================================

    def _get_path(
        self,
        conversation_id: str,
    ) -> Path:

        return (
            self.conversations_dir
            / f"{conversation_id}.json"
        )
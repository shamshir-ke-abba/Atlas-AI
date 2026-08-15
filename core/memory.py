"""
Atlas V3 Persistent Memory Manager.

Single source of truth for general user memory.

Memory is intentionally separate from fitness/nutrition profiles.
Those tools own their domain-specific profile data.
"""

import json
import logging
import re
from typing import Any, Dict, Optional

from config import MEMORY_FILE

logger = logging.getLogger(__name__)


class MemoryManager:

    def __init__(self):
        self.file = MEMORY_FILE

        self.file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.file.exists():
            self._save(self._default())

    # ==================================================
    # DEFAULT STRUCTURE
    # ==================================================

    @staticmethod
    def _default() -> Dict[str, Any]:
        return {
            "identity": {},
            "preferences": {},
            "facts": {},
            "goals": {},
        }

    # ==================================================
    # STORAGE
    # ==================================================

    def _load(self) -> Dict[str, Any]:
        try:
            with self.file.open(
                "r",
                encoding="utf-8",
            ) as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return self._default()

            return data

        except (
            FileNotFoundError,
            json.JSONDecodeError,
            OSError,
        ) as exc:
            logger.warning(
                "Could not load memory: %s",
                exc,
            )
            return self._default()

    def _save(self, data: Dict[str, Any]) -> None:
        temporary = self.file.with_suffix(".tmp")

        with temporary.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False,
            )

        temporary.replace(self.file)

    # ==================================================
    # BASIC MEMORY API
    # ==================================================

    def remember(
        self,
        category: str,
        key: str,
        value: Any,
    ) -> None:

        category = str(category or "").strip()
        key = str(key or "").strip()

        if not category or not key:
            return

        data = self._load()

        if category not in data:
            data[category] = {}

        if not isinstance(data[category], dict):
            data[category] = {}

        data[category][key] = value

        self._save(data)

        logger.info(
            "Memory saved: %s.%s",
            category,
            key,
        )

    def recall(
        self,
        category: str,
        key: str,
    ) -> Optional[Any]:

        data = self._load()

        section = data.get(
            category,
            {},
        )

        if not isinstance(section, dict):
            return None

        return section.get(key)

    def forget(
        self,
        category: str,
        key: str,
    ) -> None:

        data = self._load()

        section = data.get(category)

        if not isinstance(section, dict):
            return

        section.pop(key, None)

        if not section:
            data.pop(category, None)

        self._save(data)

    def all(self) -> Dict[str, Any]:
        return self._load()

    def clear(self) -> None:
        self._save(self._default())

    # ==================================================
    # SAFE FACT EXTRACTION
    # ==================================================

    def extract_from_message(
        self,
        message: str,
    ) -> None:
        """
        Extract explicit, high-confidence personal facts.

        We deliberately avoid broad patterns such as:
            "I'm ..."
        because those can accidentally store ordinary conversation
        as the user's name or identity.
        """

        text = " ".join(
            str(message or "").strip().split()
        )

        if not text:
            return

        # --------------------------------------------------
        # Name
        # --------------------------------------------------

        match = re.search(
            r"\bmy name is\s+([A-Za-z][A-Za-z0-9_-]*)",
            text,
            re.IGNORECASE,
        )

        if match:
            self.remember(
                "identity",
                "name",
                match.group(1).strip(),
            )

        # --------------------------------------------------
        # City / location
        # --------------------------------------------------

        match = re.search(
            r"\bi live in\s+([A-Za-z][A-Za-z .'-]*?)(?:[.!?,]|$)",
            text,
            re.IGNORECASE,
        )

        if match:
            city = match.group(1).strip()

            if city:
                self.remember(
                    "identity",
                    "city",
                    city,
                )

        # --------------------------------------------------
        # Favorite color
        # --------------------------------------------------

        match = re.search(
            r"\bmy favou?rite color is\s+(.+?)(?:[.!?,]|$)",
            text,
            re.IGNORECASE,
        )

        if match:
            value = match.group(1).strip()

            if value:
                self.remember(
                    "preferences",
                    "favorite_color",
                    value,
                )

        # --------------------------------------------------
        # Favorite food
        # --------------------------------------------------

        match = re.search(
            r"\bmy favou?rite food is\s+(.+?)(?:[.!?,]|$)",
            text,
            re.IGNORECASE,
        )

        if match:
            value = match.group(1).strip()

            if value:
                self.remember(
                    "preferences",
                    "favorite_food",
                    value,
                )

        # --------------------------------------------------
        # Explicit "remember" statements
        # --------------------------------------------------

        match = re.search(
            r"\bremember that\s+(.+?)(?:[.!?]|$)",
            text,
            re.IGNORECASE,
        )

        if match:
            fact = match.group(1).strip()

            if fact:
                facts = self._load().get(
                    "facts",
                    {},
                )

                if not isinstance(facts, dict):
                    facts = {}

                next_id = str(
                    len(facts) + 1
                )

                self.remember(
                    "facts",
                    next_id,
                    fact,
                )

    # ==================================================
    # RELEVANT MEMORY
    # ==================================================

    def relevant(
        self,
        message: str,
    ) -> Dict[str, Any]:
        """
        Return memory relevant enough to place into the
        current model context.

        For the current small model, a compact deterministic
        representation is preferable to dumping arbitrary
        data.
        """

        data = self._load()

        text = str(
            message or ""
        ).lower()

        result: Dict[str, Any] = {}

        identity = data.get(
            "identity",
            {},
        )

        preferences = data.get(
            "preferences",
            {},
        )

        facts = data.get(
            "facts",
            {},
        )

        goals = data.get(
            "goals",
            {},
        )

        # Identity questions / conversational personalization.
        if any(
            phrase in text
            for phrase in (
                "my name",
                "who am i",
                "where do i live",
                "where i live",
                "about me",
                "my profile",
            )
        ):
            if identity:
                result["identity"] = identity

        # Preference-related questions.
        if any(
            phrase in text
            for phrase in (
                "favorite",
                "favourite",
                "prefer",
                "preference",
                "like",
                "dislike",
                "food",
                "eat",
                "color",
                "colour",
            )
        ):
            if preferences:
                result["preferences"] = preferences

        # Goal-related questions.
        if any(
            phrase in text
            for phrase in (
                "goal",
                "goals",
                "plan",
                "planning",
                "want to achieve",
            )
        ):
            if goals:
                result["goals"] = goals

        # Explicit recall / remember requests should get facts.
        if any(
            phrase in text
            for phrase in (
                "remember",
                "forgot",
                "what did i tell you",
                "what do you know about me",
                "do you remember",
            )
        ):
            if facts:
                result["facts"] = facts

            if identity:
                result["identity"] = identity

            if preferences:
                result["preferences"] = preferences

            if goals:
                result["goals"] = goals

        return result

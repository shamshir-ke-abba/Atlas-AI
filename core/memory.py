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
            "projects": {},
            "environment": {},
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
        Extract explicit, high-confidence personal facts from user statements.

        This layer is intentionally conservative. It matches only clear user
        facts, not ordinary questions or temporary emotional statements.
        """

        text = " ".join(
            str(message or "").strip().split()
        )

        if not text:
            return

        lower = text.lower()

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

        # --------------------------------------------------
        # Name
        # --------------------------------------------------

        match = re.search(
            r"\b(?:my name is|i am|i'm)\s+([A-Za-z][A-Za-z0-9_-]*)",
            text,
            re.IGNORECASE,
        )

        if match:
            value = match.group(1).strip(" .,!?:;\"")

            if value:
                lowered = value.lower()
                blocked = {
                    "tired",
                    "studying",
                    "busy",
                    "building",
                    "working",
                    "using",
                    "creating",
                    "developing",
                    "making",
                    "learning",
                    "writing",
                    "exploring",
                    "researching",
                }

                if lowered not in blocked and not lowered.endswith("ing"):
                    self.remember(
                        "identity",
                        "name",
                        value,
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
        # Project / technology extraction
        # --------------------------------------------------

        project_name = None
        technology = None

        project_patterns = (
            r"\b(?:i(?:'m| am)|i work on|i'm working on|i am working on|my project|project)\s+(?:building|working on|developing|creating|making)\s+(?:an?\s+)?(?:[A-Za-z][A-Za-z0-9 _-]*?\s+)?(?:called|named)\s+([A-Za-z][A-Za-z0-9 _-]*?)(?:\s+in\s+([A-Za-z][A-Za-z0-9_.+-]+))?(?:[.!?]|$)",
            r"\bmy\s+project\s+([A-Za-z][A-Za-z0-9 _-]*?)(?:\s+(?:is|was)\s+(?:written|built|developed|created)\s+in\s+([A-Za-z][A-Za-z0-9_.+-]+)|\s+(?:is|was)\s+(?:called|named)\s+([A-Za-z][A-Za-z0-9 _-]*?))?(?:[.!?]|$)",
            r"\b(?:my\s+project|project|app|application)\s+(?:is|is called|called)\s+([A-Za-z][A-Za-z0-9 _-]*?)(?:\s+(?:written|built|developed|in|using)\s+in\s+([A-Za-z][A-Za-z0-9_.+-]+))?(?:[.!?]|$)",
            r"\b(?:i(?:'m| am)|i work on|i'm working on|i am working on)\s+(?:on|with)\s+([A-Za-z][A-Za-z0-9 _-]*?)(?:\s+in\s+([A-Za-z][A-Za-z0-9_.+-]+))?(?:[.!?]|$)",
        )

        for pattern in project_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                project_name = (match.group(1) or "").strip(" .,!?:;\"")
                technology = (match.group(2) or match.group(3) or "").strip(" .,!?:;\"")
                if project_name:
                    break

        if project_name:
            self.remember(
                "projects",
                "project_name",
                project_name,
            )

        if technology:
            self.remember(
                "projects",
                "technology",
                technology,
            )

        # --------------------------------------------------
        # Preference extraction (conservative)
        # --------------------------------------------------

        for style, key in (
            ("first principles", "explanation_style"),
            ("step by step", "explanation_style"),
            ("step-by-step", "explanation_style"),
            ("concise", "explanation_style"),
            ("detailed", "explanation_style"),
            ("practical", "explanation_style"),
        ):
            if style in lower and re.search(
                r"\b(?:i prefer|i like|i enjoy|i value|i usually prefer|i want)\b",
                lower,
            ):
                self.remember(
                    "preferences",
                    key,
                    style,
                )
                break

        # --------------------------------------------------
        # Environment extraction (OS only)
        # --------------------------------------------------

        os_names = (
            "ubuntu",
            "windows",
            "macos",
            "linux",
            "debian",
            "fedora",
        )

        for os_name in os_names:
            if os_name in lower and re.search(
                r"\b(?:i use|i usually use|i run|i work on|i work with|my operating system|os)\b",
                lower,
            ):
                self.remember(
                    "environment",
                    "operating_system",
                    os_name.title() if os_name != "macos" else "macOS",
                )
                break

        # --------------------------------------------------
        # Keep explicit facts from low-level remember commands
        # --------------------------------------------------

        if "remember that" not in lower and "my name is" not in lower:
            if re.search(r"\b(?:i use|i prefer|i like|i enjoy)\b", lower):
                pass

    # ==================================================
    # RELEVANT MEMORY
    # ==================================================

    def relevant(
        self,
        message: str,
    ) -> Dict[str, Any]:
        """
        Return only the user memory segments relevant to the current request.

        This deliberately avoids dumping the entire memory database into every
        prompt. The filter is conservative and deterministic.
        """

        data = self._load()

        text = str(
            message or ""
        ).lower()

        if not text:
            return {}

        result: Dict[str, Any] = {}

        identity = data.get("identity", {})
        preferences = data.get("preferences", {})
        projects = data.get("projects", {})
        environment = data.get("environment", {})
        facts = data.get("facts", {})
        goals = data.get("goals", {})

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
        ) and identity:
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
        ) and preferences:
            result["preferences"] = preferences

        # Project / technology questions.
        if (
            (
                "project" in text
                or "app" in text
                or "application" in text
                or "software" in text
                or "codebase" in text
                or "structure" in text
            )
            and (
                "python" in text
                or "project" in text
                or "code" in text
            )
            and projects
        ):
            result["projects"] = projects

        # Environment-related queries.
        if any(
            phrase in text
            for phrase in (
                "ubuntu",
                "windows",
                "macos",
                "linux",
                "operating system",
                "os",
            )
        ) and environment:
            result["environment"] = environment

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
        ) and goals:
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

            if projects:
                result["projects"] = projects

            if environment:
                result["environment"] = environment

            if goals:
                result["goals"] = goals

        return result

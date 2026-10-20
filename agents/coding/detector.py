"""Coding task detection for Atlas V3.

This module decides whether a user message is requesting
software-engineering work on the repository or workspace filesystem operations.
Ordinary programming questions (e.g. asking to write a function snippet in chat
or explaining architecture/design) are kept as normal conversations.
"""

import re


class CodingTaskDetector:
    """Conservative detector for explicit coding tasks and workspace filesystem operations."""

    STRONG_PATTERNS = (
        r"\bfix\s+(?:the\s+)?(?:bug|error|issue|problem)\b",
        r"\bdebug\b",
        r"\bdebugging\b",
        r"\brefactor\b",
        r"\bimplement\b",
        r"\bmodify\b",
        r"\bedit\b",
        r"\bchange\b.*\b(?:code|file|function|class)\b",
        r"\badd\b.*\b(?:feature|function|class|test)\b",
        r"\bwrite\b.*\b(?:file)\b",
        r"\bcreate\b.*\b(?:file|directory|folder)\b",
        r"\brun\b.*\b(?:pytest|tests?|test suite)\b",
        r"\b(?:pytest|test suite)\b.*\b(?:fail|failing|failure|error)\b",
        r"\binspect\b.*\b(?:repo|repository|codebase|code|project)\b",
        r"\banaly[sz]e\b.*\b(?:repo|repository|codebase|code|project|error)\b",
        r"\bwhy\s+(?:is|does|did)\b.*\b(?:code|python|function|test|error)\b",
        r"\blist\b.*\b(?:files|directories|folders)\b",
        r"\bread\b.*\b(?:file|contents)\b",
        r"\bfilesystem\b",
    )

    def is_coding_task(self, message: str) -> bool:
        """Return True only for explicit coding requests and filesystem operations."""
        text = self._normalize(message)

        if not text:
            return False

        # Exclude purely explanatory/design questions unless explicit filesystem/fix actions are asked
        if any(
            text.startswith(prefix)
            for prefix in (
                "explain",
                "what is",
                "what are",
                "tell me",
                "teach me",
                "describe",
                "design a",
            )
        ) and not any(
            re.search(pat, text, re.IGNORECASE)
            for pat in (
                r"\bcreate\s+file\b",
                r"\bwrite\s+file\b",
                r"\bmodify\s+file\b",
                r"\bedit\s+file\b",
                r"\bfix\b",
                r"\bdebug\b",
                r"\blist\s+files\b",
                r"\brun\s+(?:tests?|pytest)\b",
            )
        ):
            return False

        return any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in self.STRONG_PATTERNS
        )

    @staticmethod
    def _normalize(message: str) -> str:
        return " ".join(
            str(message or "")
            .strip()
            .split()
        ).lower()

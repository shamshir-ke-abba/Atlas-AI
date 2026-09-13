"""
Coding task detection for Atlas V3.

This module only decides whether a user message is likely asking
Atlas to perform software-engineering work.

It does not execute code, modify files, or call the model.
"""

import re


class CodingTaskDetector:
    """Conservative detector for explicit coding tasks."""

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
        r"\bwrite\b.*\b(?:code|function|class|test|script)\b",
        r"\bcreate\b.*\b(?:file|function|class|test|script)\b",
        r"\brun\b.*\b(?:pytest|tests?|test suite)\b",
        r"\b(?:pytest|test suite)\b.*\b(?:fail|failing|failure|error)\b",
        r"\binspect\b.*\b(?:repo|repository|codebase|code|project)\b",
        r"\banaly[sz]e\b.*\b(?:repo|repository|codebase|code|project|error)\b",
        r"\bwhy\s+(?:is|does|did)\b.*\b(?:code|python|function|test|error)\b",
    )

    CODE_CONTEXT_PATTERNS = (
        r"\bpython\b",
        r"\bjavascript\b",
        r"\btypescript\b",
        r"\bjava\b",
        r"\bc\+\+\b",
        r"\brust\b",
        r"\bgo\b",
        r"\bcode\b",
        r"\bfunction\b",
        r"\bclass\b",
        r"\bvariable\b",
        r"\bexception\b",
        r"\btraceback\b",
        r"\bstack trace\b",
        r"\bpytest\b",
        r"\bgit\b",
        r"\brepository\b",
        r"\bcodebase\b",
    )

    def is_coding_task(self, message: str) -> bool:
        """
        Return True only for reasonably explicit coding requests.

        The detector is intentionally conservative so ordinary
        programming questions remain normal Atlas conversations.
        """

        text = self._normalize(message)

        if not text:
            return False

        if any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in self.STRONG_PATTERNS
        ):
            return True

        code_context_count = sum(
            bool(
                re.search(
                    pattern,
                    text,
                    re.IGNORECASE,
                )
            )
            for pattern in self.CODE_CONTEXT_PATTERNS
        )

        action_words = (
            "help",
            "show",
            "explain",
            "tell",
            "how",
            "why",
        )

        has_action = any(
            word in text.split()
            for word in action_words
        )

        return (
            code_context_count >= 2
            and has_action
        )

    @staticmethod
    def _normalize(message: str) -> str:
        return " ".join(
            str(message or "")
            .strip()
            .split()
        ).lower()


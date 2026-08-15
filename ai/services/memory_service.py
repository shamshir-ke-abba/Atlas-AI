"""Backward-compatible memory service adapter.

This module exposes the original `MemoryService` interface but delegates
to the canonical `core.memory.MemoryManager`. This preserves imports and
behaviour expected by other parts of the codebase while centralizing
persistent storage.
"""

from typing import Any, Dict, Optional
from core.memory import MemoryManager


class MemoryService:
    """Thin adapter around core.memory.MemoryManager."""

    def __init__(self):
        self._mgr = MemoryManager()

    def extract(self, message: str) -> None:
        extractor = getattr(self._mgr, "extract_from_message", None)
        if callable(extractor):
            extractor(message)

    def try_recall(self, message: str) -> Optional[str]:
        relevant = getattr(self._mgr, "relevant", None)
        if callable(relevant):
            rel = relevant(message)
            if rel.get("identity"):
                name = rel["identity"].get("name")
                if name:
                    return f"You are {name}."

        # Fallbacks
        try:
            name = self._mgr.recall("identity", "name")
            if name:
                return f"Your name is {name}."
        except Exception:
            pass

        return None

    def remember(self, category: str, key: str, value: Any) -> None:
        return self._mgr.remember(category, key, value)

    def recall(self, category: str, key: str) -> Optional[Any]:
        return self._mgr.recall(category, key)

    def all(self) -> Dict[str, Any]:
        return self._mgr.all()
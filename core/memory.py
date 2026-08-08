"""
Atlas V3 Memory Manager

Persistent user memory stored in the configured data directory.
"""

import json

from config import MEMORY_FILE


class MemoryManager:

    def __init__(self):
        self.file = MEMORY_FILE

        self.file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.file.exists():
            self._save({})

        else:
            try:
                data = self._load()

                if not isinstance(data, dict):
                    self._save({})

            except (json.JSONDecodeError, OSError):
                self._save({})

    # --------------------------------------------------
    # Internal
    # --------------------------------------------------

    def _load(self):
        try:
            with self.file.open(
                "r",
                encoding="utf-8",
            ) as f:
                data = json.load(f)

            return data if isinstance(data, dict) else {}

        except (
            FileNotFoundError,
            json.JSONDecodeError,
            OSError,
        ):
            return {}

    def _save(self, data):
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

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def remember(
        self,
        category,
        key,
        value,
    ):
        data = self._load()

        if category not in data:
            data[category] = {}

        data[category][key] = value

        self._save(data)

    def recall(
        self,
        category,
        key,
    ):
        data = self._load()

        return data.get(
            category,
            {},
        ).get(key)

    def forget(
        self,
        category,
        key,
    ):
        data = self._load()

        if category not in data:
            return

        data[category].pop(
            key,
            None,
        )

        if not data[category]:
            del data[category]

        self._save(data)

    def all(self):
        return self._load()

    def clear(self):
        self._save({})
from pathlib import Path
from typing import List


DEFAULT_IGNORED = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
}


class RepositoryContext:
    def __init__(self, root):
        self.root = Path(root).resolve()

    def list_files(self, max_files: int = 500) -> List[str]:
        files = []

        for path in self.root.rglob("*"):
            if not path.is_file():
                continue

            relative = path.relative_to(self.root)

            if any(part in DEFAULT_IGNORED for part in relative.parts):
                continue

            files.append(relative.as_posix())

            if len(files) >= max_files:
                break

        files.sort()
        return files

    def read_file(self, path, max_chars: int = 30000) -> str:
        target = self._resolve(path)

        if not target.is_file():
            raise FileNotFoundError(
                f"File does not exist: {path}"
            )

        text = target.read_text(
            encoding="utf-8",
            errors="replace",
        )

        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[FILE TRUNCATED]"

        return text

    def search(self, query, max_results: int = 100):
        query = str(query or "").strip()

        if not query:
            return []

        results = []

        for path in self.root.rglob("*"):
            if not path.is_file():
                continue

            relative = path.relative_to(self.root)

            if any(part in DEFAULT_IGNORED for part in relative.parts):
                continue

            try:
                text = path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            except Exception:
                continue

            for line_number, line in enumerate(
                text.splitlines(),
                start=1,
            ):
                if query.lower() not in line.lower():
                    continue

                results.append(
                    {
                        "file": relative.as_posix(),
                        "line": line_number,
                        "text": line.strip(),
                    }
                )

                if len(results) >= max_results:
                    return results

        return results

    def _resolve(self, path):
        target = Path(path)

        if not target.is_absolute():
            target = self.root / target

        target = target.resolve()

        try:
            target.relative_to(self.root)
        except ValueError:
            raise PermissionError(
                "Requested path escapes repository root."
            )

        return target

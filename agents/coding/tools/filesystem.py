from pathlib import Path


class CodeFilesystem:
    """Safe filesystem access for the coding agent."""

    def __init__(self, workspace):
        self.workspace = Path(workspace).resolve()

    def _safe_path(self, path):
        target = (self.workspace / path).resolve()

        if target != self.workspace and self.workspace not in target.parents:
            raise PermissionError(
                f"Path outside workspace: {path}"
            )

        return target

    def list_files(self, path="."):
        directory = self._safe_path(path)

        if not directory.is_dir():
            raise NotADirectoryError(str(directory))

        results = []

        for item in sorted(directory.iterdir()):
            if item.name in {
                ".git",
                ".venv",
                "venv",
                "__pycache__",
                ".pytest_cache",
                "node_modules",
            }:
                continue

            results.append(
                {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                }
            )

        return results

    def read_file(self, path):
        target = self._safe_path(path)

        if not target.is_file():
            raise FileNotFoundError(str(target))

        return target.read_text(
            encoding="utf-8"
        )

from pathlib import Path

from .permissions import CodingPermissions, ensure_inside_root


class CodingEditor:
    """Safely modify files inside the coding-agent workspace."""

    def __init__(self, root, permissions=None):
        self.root = Path(root).resolve()

        self.permissions = (
            permissions
            if permissions is not None
            else CodingPermissions()
        )

    def write_file(self, path, content):
        """Replace a file's contents after permission and path checks."""

        self.permissions.check_write()

        target = Path(path)

        if not target.is_absolute():
            target = self.root / target

        target = ensure_inside_root(
            self.root,
            target,
        )

        if not target.is_file():
            raise FileNotFoundError(
                f"File does not exist: {path}"
            )

        target.write_text(
            str(content),
            encoding="utf-8",
        )

        return {
            "success": True,
            "path": target.relative_to(
                self.root
            ).as_posix(),
        }

    def replace_text(
        self,
        path,
        old_text,
        new_text,
    ):
        """Replace one exact text occurrence in a file."""

        self.permissions.check_write()

        target = Path(path)

        if not target.is_absolute():
            target = self.root / target

        target = ensure_inside_root(
            self.root,
            target,
        )

        if not target.is_file():
            raise FileNotFoundError(
                f"File does not exist: {path}"
            )

        text = target.read_text(
            encoding="utf-8",
            errors="replace",
        )

        if old_text not in text:
            raise ValueError(
                "The requested text was not found."
            )

        if text.count(old_text) != 1:
            raise ValueError(
                "The requested text occurs more than once."
            )

        updated = text.replace(
            old_text,
            new_text,
            1,
        )

        target.write_text(
            updated,
            encoding="utf-8",
        )

        return {
            "success": True,
            "path": target.relative_to(
                self.root
            ).as_posix(),
        }
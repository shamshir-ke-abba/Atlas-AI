from dataclasses import dataclass
from pathlib import Path


@dataclass
class CodingPermissions:
    allow_read: bool = True
    allow_search: bool = True
    allow_list: bool = True
    allow_write: bool = False
    allow_tests: bool = False
    allow_git: bool = False

    def check_read(self):
        if not self.allow_read:
            raise PermissionError(
                "Coding Agent does not have permission to read files."
            )

    def check_search(self):
        if not self.allow_search:
            raise PermissionError(
                "Coding Agent does not have permission to search files."
            )

    def check_list(self):
        if not self.allow_list:
            raise PermissionError(
                "Coding Agent does not have permission to list files."
            )

    def check_write(self):
        if not self.allow_write:
            raise PermissionError(
                "Coding Agent does not have permission to modify files."
            )

    def check_tests(self):
        if not self.allow_tests:
            raise PermissionError(
                "Coding Agent does not have permission to run tests."
            )

    def check_git(self):
        if not self.allow_git:
            raise PermissionError(
                "Coding Agent does not have permission to perform git operations."
            )


def ensure_inside_root(root: Path, target: Path) -> Path:
    root = root.resolve()
    target = target.resolve()

    try:
        target.relative_to(root)
    except ValueError:
        raise PermissionError(
            f"Path escapes repository root: {target}"
        )

    return target

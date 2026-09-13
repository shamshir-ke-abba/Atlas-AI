from dataclasses import dataclass

from agents.coding.permissions import CodingPermissions


@dataclass
class CodingPermissionRequest:
    allow_write: bool = False
    allow_tests: bool = False
    allow_git: bool = False


class CodingPermissionManager:
    """Create coding permissions from an explicit user approval."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._approved = CodingPermissionRequest()

    def approve(
        self,
        allow_write=False,
        allow_tests=False,
        allow_git=False,
    ):
        self._approved = CodingPermissionRequest(
            allow_write=bool(allow_write),
            allow_tests=bool(allow_tests),
            allow_git=bool(allow_git),
        )

    def permissions(self):
        return CodingPermissions(
            allow_read=True,
            allow_search=True,
            allow_list=True,
            allow_write=self._approved.allow_write,
            allow_tests=self._approved.allow_tests,
            allow_git=self._approved.allow_git,
        )

    def needs_write_permission(self):
        return not self._approved.allow_write

    def needs_test_permission(self):
        return not self._approved.allow_tests

    def needs_git_permission(self):
        return not self._approved.allow_git

    def status(self):
        return {
            "read": True,
            "search": True,
            "list": True,
            "write": self._approved.allow_write,
            "tests": self._approved.allow_tests,
            "git": self._approved.allow_git,
        }

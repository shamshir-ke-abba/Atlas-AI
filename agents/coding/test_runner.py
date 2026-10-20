import subprocess
from pathlib import Path

from .permissions import CodingPermissions, ensure_inside_root


class CodingTestRunner:
    """Run pytest safely inside the coding-agent workspace."""

    def __init__(self, root, permissions=None):
        self.root = Path(root).resolve()

        self.permissions = (
            permissions
            if permissions is not None
            else CodingPermissions()
        )

    def run(self, test_path="tests"):
        """Run pytest and return structured test results."""

        self.permissions.check_tests()

        target = Path(test_path)

        if not target.is_absolute():
            target = self.root / target

        target = ensure_inside_root(
            self.root,
            target,
        )

        if not target.exists():
            raise FileNotFoundError(
                f"Test path does not exist: {test_path}"
            )

        import sys

        command = [
            sys.executable,
            "-m",
            "pytest",
            str(target.relative_to(self.root)),
            "-q",
        ]

        try:
            completed = subprocess.run(
                command,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "success": False,
                "returncode": None,
                "stdout": exc.stdout or "",
                "stderr": (
                    exc.stderr or ""
                ),
                "timeout": True,
                "summary": "Test run timed out.",
            }

        output = "\n".join(
            part
            for part in (
                completed.stdout.strip(),
                completed.stderr.strip(),
            )
            if part
        )

        return {
            "success": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timeout": False,
            "summary": (
                "Tests passed."
                if completed.returncode == 0
                else "Tests failed."
            ),
            "output": output,
        }
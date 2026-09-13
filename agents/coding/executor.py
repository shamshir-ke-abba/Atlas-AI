from pathlib import Path

from .context import RepositoryContext
from .editor import CodingEditor
from .error_analyzer import CodingErrorAnalyzer
from .permissions import CodingPermissions
from .test_runner import CodingTestRunner


class CodingExecutor:
    """Execute permission-controlled coding operations."""

    def __init__(self, root, permissions=None):
        self.root = Path(root).resolve()

        self.permissions = (
            permissions
            if permissions is not None
            else CodingPermissions()
        )

        self.context = RepositoryContext(
            self.root
        )

        self.editor = CodingEditor(
            self.root,
            permissions=self.permissions,
        )

        self.test_runner = CodingTestRunner(
            self.root,
            permissions=self.permissions,
        )

        self.error_analyzer = CodingErrorAnalyzer()

    def read_file(self, path):
        """Read a file through the repository context."""
        self.permissions.check_read()

        return self.context.read_file(
            path
        )

    def list_files(self):
        """List repository files."""
        self.permissions.check_list()

        return self.context.list_files()

    def search(self, query):
        """Search repository contents."""
        self.permissions.check_search()

        return self.context.search(
            query
        )

    def write_file(self, path, content):
        """Delegate file replacement to the editor."""
        return self.editor.write_file(
            path,
            content,
        )

    def replace_text(
        self,
        path,
        old_text,
        new_text,
    ):
        """Delegate exact text replacement to the editor."""
        return self.editor.replace_text(
            path,
            old_text,
            new_text,
        )

    def apply_change(self, change):
        """Apply one validated CodeChange."""

        if change is None:
            raise ValueError(
                "Cannot apply an empty change."
            )

        return self.replace_text(
            change.path,
            change.old_text,
            change.new_text,
        )

    def run_tests(self, test_path="tests"):
        """Run tests through the dedicated test runner."""
        return self.test_runner.run(
            test_path
        )

    def analyze_errors(self, test_result):
        """Analyze a test-run result."""
        return self.error_analyzer.analyze(
            test_result
        )

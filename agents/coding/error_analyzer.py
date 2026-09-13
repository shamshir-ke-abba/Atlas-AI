import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class ErrorAnalysis:
    success: bool
    error_type: str = ""
    message: str = ""
    files: List[str] = field(
        default_factory=list
    )
    lines: List[int] = field(
        default_factory=list
    )
    suggestions: List[str] = field(
        default_factory=list
    )


class CodingErrorAnalyzer:
    """Analyze pytest output and extract actionable failure information."""

    TRACEBACK_PATTERN = re.compile(
        r'File ["\']([^"\']+)["\'], line (\d+)'
    )

    def analyze(self, test_result):
        """Convert a test-run result into structured analysis."""

        if not isinstance(test_result, dict):
            return ErrorAnalysis(
                success=False,
                error_type="invalid_result",
                message="Invalid test result.",
            )

        if test_result.get("success"):
            return ErrorAnalysis(
                success=True,
                message="Tests passed.",
            )

        output = "\n".join(
            str(test_result.get(key, "") or "")
            for key in (
                "stdout",
                "stderr",
                "output",
            )
        )

        files = []
        lines = []

        for match in self.TRACEBACK_PATTERN.finditer(
            output
        ):
            file_path = match.group(1)
            line_number = int(match.group(2))

            if file_path not in files:
                files.append(file_path)

            if line_number not in lines:
                lines.append(line_number)

        error_type = self._detect_error_type(
            output
        )

        message = self._extract_message(
            output,
            error_type,
        )

        suggestions = self._suggest(
            error_type
        )

        return ErrorAnalysis(
            success=False,
            error_type=error_type,
            message=message,
            files=files,
            lines=lines,
            suggestions=suggestions,
        )

    @staticmethod
    def _detect_error_type(output):
        patterns = (
            ("AssertionError", "assertion_error"),
            ("ModuleNotFoundError", "module_not_found"),
            ("ImportError", "import_error"),
            ("SyntaxError", "syntax_error"),
            ("TypeError", "type_error"),
            ("NameError", "name_error"),
            ("AttributeError", "attribute_error"),
            ("KeyError", "key_error"),
            ("IndexError", "index_error"),
            ("FileNotFoundError", "file_not_found"),
            ("PermissionError", "permission_error"),
        )

        for marker, error_type in patterns:
            if marker in output:
                return error_type

        return "test_failure"

    @staticmethod
    def _extract_message(output, error_type):
        lines = [
            line.strip()
            for line in str(output).splitlines()
            if line.strip()
        ]

        for line in reversed(lines):
            if error_type.replace(
                "_",
                "",
            ).lower() in line.replace(
                ":",
                "",
            ).replace(
                " ",
                "",
            ).lower():
                return line

        for line in reversed(lines):
            if (
                "FAILED" in line
                or "ERROR" in line
            ):
                return line

        return "Tests failed."

    @staticmethod
    def _suggest(error_type):
        suggestions = {
            "assertion_error": [
                "Inspect the failing assertion and the values being compared.",
            ],
            "module_not_found": [
                "Check the import path and whether the dependency exists.",
            ],
            "import_error": [
                "Inspect the failing import and module exports.",
            ],
            "syntax_error": [
                "Inspect the reported file and line for invalid Python syntax.",
            ],
            "type_error": [
                "Inspect the argument types and function signature.",
            ],
            "name_error": [
                "Check whether the referenced name is defined or imported.",
            ],
            "attribute_error": [
                "Check whether the object provides the referenced attribute.",
            ],
            "key_error": [
                "Check whether the requested dictionary key exists.",
            ],
            "index_error": [
                "Check the sequence bounds before indexing.",
            ],
            "file_not_found": [
                "Check the requested path and whether the file exists.",
            ],
            "permission_error": [
                "Check the operation permissions and requested path.",
            ],
            "test_failure": [
                "Inspect the pytest output and traceback for the root cause.",
            ],
        }

        return suggestions.get(
            error_type,
            suggestions["test_failure"],
        )
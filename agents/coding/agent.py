from pathlib import Path
import re

from agents.coding.context import RepositoryContext
from agents.coding.model import CodingModel
from agents.coding.prompts import CODING_SYSTEM_PROMPT
from agents.coding.planner import CodingPlanner
from agents.coding.change_generator import CodingChangeGenerator


class CodingAgent:

    def __init__(self, workspace=None, model=None):
        self.workspace = Path(
            workspace or Path.cwd()
        ).resolve()

        self.model = model or CodingModel()

        self.context = RepositoryContext(
            self.workspace
        )

        self.planner = CodingPlanner(
            model=self.model
        )

        self.change_generator = CodingChangeGenerator(
            model=self.model
        )

    def inspect(self, task):
        """Build focused repository context for a coding task."""

        files = self.context.list_files(
            max_files=500
        )

        target_paths = self._extract_paths(
            task,
            files,
        )

        search_terms = self._extract_search_terms(
            task
        )

        relevant_files = []

        for path in target_paths:
            if path not in relevant_files:
                relevant_files.append(path)

        for term in search_terms:
            matches = self.context.search(
                term,
                max_results=20,
            )

            for match in matches:
                file_path = match["file"]

                if file_path not in relevant_files:
                    relevant_files.append(file_path)

        relevant_files = relevant_files[:50]

        file_list = "\n".join(
            f"- {path}"
            for path in files
        )

        search_results = []

        for term in search_terms:
            matches = self.context.search(
                term,
                max_results=20,
            )

            for match in matches:
                if match not in search_results:
                    search_results.append(match)

        formatted_results = "\n".join(
            f"- {item['file']}:{item['line']} "
            f"{item['text']}"
            for item in search_results[:50]
        )

        relevant_file_list = "\n".join(
            f"- {path}"
            for path in relevant_files
        )

        return f"""
PROJECT FILES:
{file_list or "No files found."}

PRIMARY TARGETS:
{relevant_file_list or "No explicit targets found."}

SEARCH RESULTS:
{formatted_results or "No relevant matches found."}
""".strip()

    @staticmethod
    def _extract_paths(task, files):
        """Find repository paths explicitly mentioned in the task."""

        text = str(task or "")

        found = []

        for file_path in files:
            if file_path in text:
                found.append(file_path)

        path_patterns = re.findall(
            r"(?:^|[\s`'\"(])"
            r"([A-Za-z0-9_.-]+"
            r"(?:/[A-Za-z0-9_.-]+)+"
            r"(?:\.[A-Za-z0-9_+-]+)?)",
            text,
        )

        for path in path_patterns:
            normalized = path.strip(
                ".,!?;:)]}"
            )

            if normalized in files and normalized not in found:
                found.append(normalized)

        return found

    @staticmethod
    def _extract_search_terms(task):
        """Extract useful repository search terms from a task."""

        words = str(task or "").split()

        stop_words = {
            "the",
            "a",
            "an",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "and",
            "or",
            "is",
            "it",
            "this",
            "that",
            "please",
            "can",
            "you",
            "me",
            "fix",
            "change",
            "modify",
            "update",
            "add",
            "implement",
            "create",
            "remove",
            "bug",
            "error",
            "issue",
            "problem",
        }

        terms = []

        for word in words:
            cleaned = word.strip(
                ".,!?;:()[]{}\"'`"
            )

            if (
                len(cleaned) >= 3
                and cleaned.lower() not in stop_words
                and cleaned not in terms
                and "/" not in cleaned
            ):
                terms.append(cleaned)

        return terms[:8]
    
    def plan(self, task):
        """Create a structured plan from repository context."""

        repository_context = self.inspect(
            task
        )

        return self.planner.create_plan(
            task,
            repository_context,
        )

    def generate_changes(self, task, plan=None):
        """Generate structured code changes without modifying files."""

        if plan is None:
            plan = self.plan(task)

        repository_context = self.inspect(
            task
        )

        return self.change_generator.generate(
            task,
            plan,
            repository_context,
        )

    def execute(
        self,
        task,
        permissions=None,
        max_attempts=2,
    ):
        """Execute a coding task through the autonomous workflow."""

        task = str(task or "").strip()

        if not task:
            return "Coding task is empty."

        if not self.model.is_available():
            return (
                f"Coding model '{self.model.model_name}' "
                "is not available in Ollama."
            )

        if permissions is None:
            from agents.coding.permission_manager import (
                CodingPermissionManager,
            )

            permission_manager = CodingPermissionManager()
            permissions = permission_manager.permissions()

        from agents.coding.workflow import CodingWorkflow

        workflow = CodingWorkflow(
            agent=self,
            permissions=permissions,
            max_attempts=max_attempts,
        )

        return workflow.run(task)

    def build_prompt(self, task):
        context = self.inspect(task)

        return f"""
{CODING_SYSTEM_PROMPT}

WORKSPACE:
{self.workspace}

USER TASK:
{task}

REPOSITORY CONTEXT:
{context}

Based ONLY on the repository information available above:

1. Identify the most relevant files.
2. Explain what should be inspected next.
3. Explain your proposed change.
4. Do not claim that you changed anything.
5. Do not invent files or code.
""".strip()

    def run(self, task):
        task = str(task or "").strip()

        if not task:
            return "Coding task is empty."

        if not self.model.is_available():
            return (
                f"Coding model '{self.model.model_name}' "
                "is not available in Ollama."
            )

        plan = self.plan(task)

        changes = self.generate_changes(
            task,
            plan,
        )

        return (
            f"OBJECTIVE:\n"
            f"{plan.objective}\n\n"
            f"FILES TO INSPECT:\n"
            f"{self._format_items(plan.files_to_inspect)}\n\n"
            f"PLANNED CHANGES:\n"
            f"{self._format_items(plan.changes)}\n\n"
            f"GENERATED CHANGES:\n"
            f"{self._format_changes(changes)}\n\n"
            f"TESTS:\n"
            f"{self._format_items(plan.tests)}\n\n"
            f"RISKS:\n"
            f"{self._format_items(plan.risks)}"
        )

    @staticmethod
    def _format_items(items):
        if not items:
            return "- None identified."

        return "\n".join(
            f"- {item}"
            for item in items
        )

    @staticmethod
    def _format_changes(change_set):
        if not change_set.changes:
            return "- No changes generated."

        results = []

        for change in change_set.changes:
            results.append(
                f"- FILE: {change.path}\n"
                f"  REASON: {change.reason}\n"
                f"  OLD_TEXT:\n"
                f"{change.old_text}\n"
                f"  NEW_TEXT:\n"
                f"{change.new_text}"
            )

        return "\n".join(results)
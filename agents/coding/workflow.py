from dataclasses import dataclass, field
from typing import List

from agents.coding.executor import CodingExecutor
from agents.coding.permissions import CodingPermissions
from agents.coding.agent import CodingAgent


@dataclass
class CodingWorkflowResult:
    success: bool
    task: str
    attempts: int = 0
    applied_changes: List[str] = field(default_factory=list)
    test_result: dict = field(default_factory=dict)
    error_analysis: object = None
    message: str = ""


class CodingWorkflow:
    """Orchestrate inspect -> plan -> change -> test -> fix."""

    def __init__(
        self,
        agent=None,
        executor=None,
        permissions=None,
        max_attempts=2,
    ):
        self.agent = agent or CodingAgent()

        self.permissions = (
            permissions
            if permissions is not None
            else CodingPermissions()
        )

        self.executor = executor or CodingExecutor(
            self.agent.workspace,
            permissions=self.permissions,
        )

        self.max_attempts = max(
            1,
            int(max_attempts),
        )

    def run(self, task):
        task = str(task or "").strip()

        if not task:
            return CodingWorkflowResult(
                success=False,
                task=task,
                message="Coding task is empty.",
            )

        applied_changes = []
        last_test_result = {}
        last_error_analysis = None

        for attempt in range(
            1,
            self.max_attempts + 1,
        ):
            plan = self.agent.plan(task)

            changes = self.agent.generate_changes(
                task,
                plan,
            )

            if not changes.changes:
                return CodingWorkflowResult(
                    success=False,
                    task=task,
                    attempts=attempt,
                    applied_changes=applied_changes,
                    test_result=last_test_result,
                    error_analysis=last_error_analysis,
                    message="No code changes were generated.",
                )

            for change in changes.changes:
                result = self.executor.apply_change(
                    change
                )

                if result.get("success"):
                    applied_changes.append(
                        result["path"]
                    )

            last_test_result = self.executor.run_tests()

            last_error_analysis = (
                self.executor.analyze_errors(
                    last_test_result
                )
            )

            if last_test_result.get("success"):
                return CodingWorkflowResult(
                    success=True,
                    task=task,
                    attempts=attempt,
                    applied_changes=applied_changes,
                    test_result=last_test_result,
                    error_analysis=last_error_analysis,
                    message="Coding task completed successfully.",
                )

            if attempt >= self.max_attempts:
                break

            task = self._build_fix_task(
                task,
                last_error_analysis,
            )

        return CodingWorkflowResult(
            success=False,
            task=task,
            attempts=self.max_attempts,
            applied_changes=applied_changes,
            test_result=last_test_result,
            error_analysis=last_error_analysis,
            message="Coding task failed after the allowed attempts.",
        )

    @staticmethod
    def _build_fix_task(
        original_task,
        error_analysis,
    ):
        error_type = getattr(
            error_analysis,
            "error_type",
            "test_failure",
        )

        message = getattr(
            error_analysis,
            "message",
            "Tests failed.",
        )

        suggestions = getattr(
            error_analysis,
            "suggestions",
            [],
        )

        suggestion_text = "\n".join(
            f"- {item}"
            for item in suggestions
        )

        return (
            f"{original_task}\n\n"
            "The previous implementation caused failing tests.\n"
            "Analyze and fix the failure.\n\n"
            f"ERROR TYPE:\n{error_type}\n\n"
            f"ERROR:\n{message}\n\n"
            f"SUGGESTIONS:\n"
            f"{suggestion_text or '- Inspect the failure traceback.'}"
        )

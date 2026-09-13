from dataclasses import dataclass

from agents.coding.change_generator import (
    CodeChange,
    ChangeSet,
)
from agents.coding.workflow import (
    CodingWorkflow,
    CodingWorkflowResult,
)


@dataclass
class FakePlan:
    objective: str = "Fix example"
    files_to_inspect: list = None
    changes: list = None
    tests: list = None
    risks: list = None

    def __post_init__(self):
        self.files_to_inspect = self.files_to_inspect or [
            "example.py"
        ]
        self.changes = self.changes or [
            "Fix example"
        ]
        self.tests = self.tests or [
            "Run pytest"
        ]
        self.risks = self.risks or []


class FakeAgent:
    def __init__(self, change_sets):
        self.workspace = "."
        self.change_sets = list(change_sets)
        self.plan_calls = 0
        self.generate_calls = 0

    def plan(self, task):
        self.plan_calls += 1
        return FakePlan()

    def generate_changes(self, task, plan=None):
        self.generate_calls += 1
        return self.change_sets.pop(0)


class FakeExecutor:
    def __init__(self, test_results):
        self.test_results = list(test_results)
        self.apply_calls = []
        self.test_calls = 0
        self.analysis_calls = 0

    def apply_change(self, change):
        self.apply_calls.append(change)
        return {
            "success": True,
            "path": change.path,
        }

    def run_tests(self):
        self.test_calls += 1
        return self.test_results.pop(0)

    def analyze_errors(self, result):
        self.analysis_calls += 1

        if result["success"]:
            return type(
                "Analysis",
                (),
                {
                    "success": True,
                    "error_type": "",
                    "message": "Tests passed.",
                    "suggestions": [],
                },
            )()

        return type(
            "Analysis",
            (),
            {
                "success": False,
                "error_type": "assertion_error",
                "message": "Assertion failed.",
                "suggestions": [
                    "Inspect the failing assertion."
                ],
            },
        )()


def make_change():
    return CodeChange(
        path="example.py",
        old_text="value = 1",
        new_text="value = 2",
        reason="Fix value",
    )


def test_empty_task_returns_failure():
    workflow = CodingWorkflow(
        agent=FakeAgent([]),
        executor=FakeExecutor([]),
    )

    result = workflow.run("")

    assert isinstance(
        result,
        CodingWorkflowResult,
    )
    assert result.success is False
    assert result.message == "Coding task is empty."


def test_successful_workflow():
    agent = FakeAgent([
        ChangeSet(
            changes=[make_change()]
        )
    ])

    executor = FakeExecutor([
        {
            "success": True,
            "returncode": 0,
        }
    ])

    workflow = CodingWorkflow(
        agent=agent,
        executor=executor,
    )

    result = workflow.run(
        "Fix example.py"
    )

    assert result.success is True
    assert result.attempts == 1
    assert result.applied_changes == [
        "example.py"
    ]
    assert executor.test_calls == 1
    assert executor.analysis_calls == 1


def test_no_changes_returns_failure():
    agent = FakeAgent([
        ChangeSet()
    ])

    executor = FakeExecutor([])

    workflow = CodingWorkflow(
        agent=agent,
        executor=executor,
    )

    result = workflow.run(
        "Fix example.py"
    )

    assert result.success is False
    assert result.attempts == 1
    assert result.message == (
        "No code changes were generated."
    )
    assert executor.test_calls == 0


def test_failed_tests_trigger_fix_attempt():
    agent = FakeAgent([
        ChangeSet(
            changes=[make_change()]
        ),
        ChangeSet(
            changes=[make_change()]
        ),
    ])

    executor = FakeExecutor([
        {
            "success": False,
            "returncode": 1,
        },
        {
            "success": True,
            "returncode": 0,
        },
    ])

    workflow = CodingWorkflow(
        agent=agent,
        executor=executor,
        max_attempts=2,
    )

    result = workflow.run(
        "Fix example.py"
    )

    assert result.success is True
    assert result.attempts == 2
    assert agent.plan_calls == 2
    assert agent.generate_calls == 2
    assert executor.test_calls == 2
    assert len(executor.apply_calls) == 2


def test_failed_workflow_stops_at_max_attempts():
    agent = FakeAgent([
        ChangeSet(
            changes=[make_change()]
        ),
        ChangeSet(
            changes=[make_change()]
        ),
    ])

    executor = FakeExecutor([
        {
            "success": False,
            "returncode": 1,
        },
        {
            "success": False,
            "returncode": 1,
        },
    ])

    workflow = CodingWorkflow(
        agent=agent,
        executor=executor,
        max_attempts=2,
    )

    result = workflow.run(
        "Fix example.py"
    )

    assert result.success is False
    assert result.attempts == 2
    assert executor.test_calls == 2
    assert agent.generate_calls == 2

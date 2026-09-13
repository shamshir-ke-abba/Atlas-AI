from dataclasses import dataclass

from agents.coding.agent import CodingAgent
from agents.coding.change_generator import (
    ChangeSet,
    CodeChange,
)
from agents.coding.permissions import CodingPermissions


class FakeModel:
    model_name = "fake"

    def is_available(self):
        return True


@dataclass
class FakePlan:
    objective: str = "Fix example"
    files_to_inspect: list = None
    changes: list = None
    tests: list = None
    risks: list = None

    def __post_init__(self):
        self.files_to_inspect = self.files_to_inspect or []
        self.changes = self.changes or []
        self.tests = self.tests or ["Run pytest"]
        self.risks = self.risks or []


class FakeAgentExecutor:
    pass


def make_agent(tmp_path):
    return CodingAgent(
        workspace=tmp_path,
        model=FakeModel(),
    )


def test_execute_empty_task(tmp_path):
    agent = make_agent(tmp_path)

    result = agent.execute("")

    assert result == "Coding task is empty."


def test_execute_returns_workflow_result(tmp_path):
    agent = make_agent(tmp_path)

    class FakeWorkflow:
        def __init__(
            self,
            agent,
            permissions=None,
            max_attempts=2,
        ):
            self.agent = agent
            self.permissions = permissions
            self.max_attempts = max_attempts

        def run(self, task):
            return "workflow executed: " + task

    original_import = __import__

    def fake_import(
        name,
        globals=None,
        locals=None,
        fromlist=(),
        level=0,
    ):
        if name == "agents.coding.workflow":
            return type(
                "Module",
                (),
                {"CodingWorkflow": FakeWorkflow},
            )()

        return original_import(
            name,
            globals,
            locals,
            fromlist,
            level,
        )

    import builtins

    original = builtins.__import__
    builtins.__import__ = fake_import

    try:
        result = agent.execute(
            "Fix example.py"
        )
    finally:
        builtins.__import__ = original

    assert result == (
        "workflow executed: Fix example.py"
    )


def test_execute_passes_permissions_and_attempts(tmp_path):
    agent = make_agent(tmp_path)

    permissions = CodingPermissions(
        allow_write=True,
        allow_tests=True,
        allow_git=False,
    )

    class FakeWorkflow:
        captured = None

        def __init__(
            self,
            agent,
            permissions=None,
            max_attempts=2,
        ):
            FakeWorkflow.captured = (
                agent,
                permissions,
                max_attempts,
            )

        def run(self, task):
            return task

    original_import = __import__

    def fake_import(
        name,
        globals=None,
        locals=None,
        fromlist=(),
        level=0,
    ):
        if name == "agents.coding.workflow":
            return type(
                "Module",
                (),
                {"CodingWorkflow": FakeWorkflow},
            )()

        return original_import(
            name,
            globals,
            locals,
            fromlist,
            level,
        )

    import builtins

    original = builtins.__import__
    builtins.__import__ = fake_import

    try:
        result = agent.execute(
            "Fix it",
            permissions=permissions,
            max_attempts=3,
        )
    finally:
        builtins.__import__ = original

    assert result == "Fix it"

    captured_agent, captured_permissions, attempts = (
        FakeWorkflow.captured
    )

    assert captured_agent is agent
    assert captured_permissions is permissions
    assert attempts == 3

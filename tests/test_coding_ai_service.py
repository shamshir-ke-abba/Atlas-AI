from agents.coding.permissions import CodingPermissions
from core.ai_service import AIService


class FakeWorker:
    def __init__(self):
        self.received = []

    def process_coding(self, task, permissions, max_attempts):
        self.received.append(
            (task, permissions, max_attempts)
        )


def test_ai_service_exposes_coding_signals():
    service = AIService()

    assert hasattr(service, "coding_requested")
    assert hasattr(service, "coding_result")
    assert hasattr(service, "coding_error")
    assert hasattr(service, "coding_finished")

    service.stop()


def test_ai_service_execute_coding_rejects_empty_task():
    service = AIService()

    service.start()

    service.execute_coding(
        "",
        CodingPermissions(),
    )

    service.stop()


def test_ai_service_execute_coding_starts_worker():
    service = AIService()

    calls = []

    service.start = lambda: calls.append("start")

    service.execute_coding(
        "Fix the bug",
        CodingPermissions(
            allow_write=True,
            allow_tests=True,
        ),
        max_attempts=3,
    )

    assert calls == ["start"]

    service.stop()


def test_ai_service_coding_request_reaches_worker():
    service = AIService()

    received = []

    def capture(task, permissions, max_attempts):
        received.append(
            (task, permissions, max_attempts)
        )

    service.worker.process_coding = capture

    # Reconnect through a direct Python callback for this unit test.
    service.coding_requested.connect(
        service.worker.process_coding
    )

    service.start()

    permissions = CodingPermissions(
        allow_write=True,
        allow_tests=True,
    )

    service.execute_coding(
        "Fix the bug",
        permissions,
        max_attempts=4,
    )

    service.stop()

    assert received
    task, received_permissions, attempts = received[-1]

    assert task == "Fix the bug"
    assert received_permissions is permissions
    assert attempts == 4

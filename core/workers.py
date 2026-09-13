"""Atlas V3 AI worker running outside the GUI thread."""

from threading import Event

from PySide6.QtCore import QObject, Signal, Slot

from ai.brain import AtlasBrain
from agents.coding.agent import CodingAgent
from core.memory import MemoryManager
from core.logger import logger


class AIWorker(QObject):
    chunk = Signal(str)
    error = Signal(str)
    finished = Signal()

    coding_result = Signal(object)
    coding_error = Signal(str)
    coding_finished = Signal()

    def __init__(self, tools=None):
        super().__init__()
        self.tools = tools
        # Inject the canonical persistent MemoryManager so the Brain
        # has a single source of truth for persistent memory.
        self.brain = AtlasBrain(
            tools=tools,
            memory=MemoryManager(),
        )
        self.coding_agent = CodingAgent()
        self.stop_event = Event()
        logger.info("AIWorker initialized with tool system")

    def request_stop(self):
        """Thread-safe cancellation request, including an in-flight HTTP call."""
        self.stop_event.set()
        try:
            self.brain.model.cancel_current()
        except Exception:
            pass

    @Slot(str)
    def process(self, message):
        self.stop_event.clear()
        try:
            for chunk in self.brain.stream_message(
                message,
            ):
                if self.stop_event.is_set():
                    break
                if chunk:
                    self.chunk.emit(str(chunk))
        except Exception as exc:
            logger.exception("AIWorker processing failed")
            self.error.emit(str(exc))
        finally:
            self.finished.emit()

    @Slot(str, object, int)
    def process_coding(
        self,
        task,
        permissions,
        max_attempts=2,
    ):
        """Execute an approved Coding Agent task in the worker thread."""

        self.stop_event.clear()

        try:
            from agents.coding.permissions import CodingPermissions

            if not isinstance(
                permissions,
                CodingPermissions,
            ):
                raise TypeError(
                    "Coding Agent requires CodingPermissions."
                )

            result = self.coding_agent.execute(
                task,
                permissions=permissions,
                max_attempts=max_attempts,
            )

            self.coding_result.emit(result)

        except Exception as exc:
            logger.exception(
                "Coding Agent execution failed"
            )
            self.coding_error.emit(str(exc))

        finally:
            self.coding_finished.emit()

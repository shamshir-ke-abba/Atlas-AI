"""Atlas V3 AI worker running outside the GUI thread."""

from threading import Event

from PySide6.QtCore import QObject, Signal, Slot

from ai.brain import AtlasBrain
from core.logger import logger


class AIWorker(QObject):
    chunk = Signal(str)
    error = Signal(str)
    finished = Signal()

    def __init__(self, tools=None):
        super().__init__()
        self.tools = tools
        self.brain = AtlasBrain(tools=tools)
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

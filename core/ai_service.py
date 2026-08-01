"""
Atlas V3 AI Service
"""

from PySide6.QtCore import QObject, Signal, QThread

from core.workers import AIWorker
from core.logger import logger


class AIService(QObject):

    chunk_ready = Signal(str)
    finished = Signal()

    generate_requested = Signal(str)

    def __init__(
        self,
        bus,
        state,
    ):

        super().__init__()

        self.bus = bus
        self.state = state

        self.thread = QThread()

        self.worker = AIWorker()

        self.worker.moveToThread(
            self.thread
        )

        # -----------------------------
        # Signals
        # -----------------------------

        self.generate_requested.connect(
            self.worker.process
        )

        self.worker.chunk.connect(
            self.chunk_ready.emit
        )

        self.worker.finished.connect(
            self.finished.emit
        )

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def start(self):

        self.thread.start()

        logger.info(
            "AI Thread started."
        )

    def stop(self):

        self.thread.quit()
        self.thread.wait()

        logger.info(
            "AI Thread stopped."
        )

    # --------------------------------------------------
    # AI
    # --------------------------------------------------

    def generate(
        self,
        message,
    ):

        self.generate_requested.emit(
            message
        )
"""
Atlas V3 AI Service
"""

from PySide6.QtCore import QObject, Signal, QThread

from core.workers import AIWorker
from core.logger import logger


class AIService(QObject):

    response_ready = Signal(str)
    generate_requested = Signal(str)

    def __init__(
        self,
        bus,
        state,
    ):

        super().__init__()

        self.bus = bus
        self.state = state

        # -----------------------------
        # Thread
        # -----------------------------

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

        self.worker.finished.connect(
            self.response_ready.emit
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
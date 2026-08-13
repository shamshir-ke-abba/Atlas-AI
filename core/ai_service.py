# core/ai_service.py

import logging

from PySide6.QtCore import (
    QObject,
    QThread,
    Signal,
)

from core.workers import AIWorker


logger = logging.getLogger("atlas")


class AIService(QObject):
    """
    AI service for Atlas.

    Owns the AI worker and provides a clean
    synchronous API for Controller while
    retaining Qt signals for GUI/streaming use.
    """

    # =========================================================
    # NORMAL AI SIGNALS
    # =========================================================

    chunk_ready = Signal(str)

    finished = Signal()

    error = Signal(str)

    # =========================================================
    # TOOL AI SIGNALS
    # =========================================================

    tool_response = Signal(str)

    tool_chunk_ready = Signal(str)

    tool_finished = Signal()

    tool_error = Signal(str)

    # =========================================================
    # REQUEST SIGNALS
    # =========================================================

    generate_requested = Signal(str)

    tool_requested = Signal(str)

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        bus=None,
        state=None,
    ):

        super().__init__()

        self.bus = bus
        self.state = state

        # -----------------------------------------------------
        # Conversation context
        # -----------------------------------------------------

        self.conversation_id = None
        self.conversation_history = []

        # -----------------------------------------------------
        # Worker thread
        # -----------------------------------------------------

        self.thread = QThread()

        self.worker = AIWorker()

        self.worker.moveToThread(
            self.thread
        )

        # -----------------------------------------------------
        # Normal AI
        # -----------------------------------------------------

        self.generate_requested.connect(
            self.worker.process
        )

        self.worker.chunk.connect(
            self.chunk_ready.emit
        )

        self.worker.finished.connect(
            self.finished.emit
        )

        self.worker.error.connect(
            self.error.emit
        )

        # -----------------------------------------------------
        # Tool AI
        # -----------------------------------------------------

        self.tool_requested.connect(
            self.worker.process_tool
        )

        self.worker.tool_chunk.connect(
            self.tool_chunk_ready.emit
        )

        self.worker.tool_finished.connect(
            self.tool_finished.emit
        )

        self.worker.tool_error.connect(
            self.tool_error.emit
        )

    # =========================================================
    # CONVERSATION
    # =========================================================

    def set_conversation(
        self,
        conversation_id,
        history,
    ):
        """
        Set the conversation context used by AtlasBrain.
        """

        self.conversation_id = (
            conversation_id
        )

        self.conversation_history = list(
            history or []
        )

        self.worker.set_conversation(
            conversation_id,
            self.conversation_history,
        )

    def clear_conversation(self):

        self.conversation_id = None

        self.conversation_history = []

        self.worker.clear_conversation()

    # =========================================================
    # LIFECYCLE
    # =========================================================

    def start(self):

        if self.thread.isRunning():
            return

        logger.info(
            "Starting AI worker thread..."
        )

        self.thread.start()

        logger.info(
            "AI worker thread started."
        )

    def stop(self):

        if not self.thread.isRunning():
            return

        logger.info(
            "Stopping AI worker thread..."
        )

        self.thread.quit()

        self.thread.wait()

        logger.info(
            "AI worker thread stopped."
        )

    # =========================================================
    # SYNCHRONOUS AI
    # =========================================================

    def process_message(
        self,
        message: str,
    ) -> str:
        """
        Process a message synchronously.

        This is intentionally executed directly through
        the worker's brain so Controller can receive a
        complete response.
        """

        return self.worker.process_sync(
            message,
            self.conversation_history,
        )

    # =========================================================
    # ASYNC NORMAL AI
    # =========================================================

    def generate(
        self,
        message: str,
    ):

        self.generate_requested.emit(
            message
        )

    # =========================================================
    # TOOL AI
    # =========================================================

    def generate_tool(
        self,
        message: str,
    ):

        self.tool_requested.emit(
            message
        )

    # =========================================================
    # BRAIN ACCESS
    # =========================================================

    @property
    def brain(self):
        """
        Compatibility property.

        Existing Atlas code may access:

            controller.ai.brain
        """

        return self.worker.brain
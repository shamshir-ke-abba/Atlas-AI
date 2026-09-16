"""
Atlas V3 AI Service

Owns the background AI worker and provides a clean Qt-signal
interface to the Controller.

Architecture:

    Controller
        |
        | generate(message)
        v
    AIService
        |
        v
    QThread
        |
        v
    AIWorker
        |
        v
    AtlasBrain
        |
        +---- Model
        +---- Tools
        |
        v
    AIService signals
        |
        v
    Controller
        |
        v
    EventBus
"""

from PySide6.QtCore import (
    QObject,
    Signal,
    QThread,
)

from core.workers import AIWorker
from core.tool_manager import ToolManager
from core.logger import logger


class AIService(QObject):
    """
    Background AI generation service.

    IMPORTANT:
    AIService deliberately does NOT subscribe to MessageReceived.

    The Controller is the single owner of user-message routing.
    This prevents the same message from being sent to the AI twice.
    """

    # ------------------------------------------------------
    # Signals exposed to Controller
    # ------------------------------------------------------

    chunk_ready = Signal(str, str)

    finished = Signal(str)

    error = Signal(str, str)

    # Internal request signal.
    #
    # This is emitted from the GUI/controller thread and connected
    # to AIWorker.process() in the worker thread.
    generate_requested = Signal(str, str)
    coding_requested = Signal(str, object, int)
    coding_result = Signal(object)
    coding_error = Signal(str)
    coding_finished = Signal()

    def __init__(
        self,
        bus=None,
        state=None,
        profile_store=None,
        parent=None,
    ):

        super().__init__(parent)

        self.bus = bus
        self.state = state

        # --------------------------------------------------
        # Tools
        # --------------------------------------------------

        self.tools = ToolManager()

        if profile_store is not None:
            self.tools.attach_profile_store(profile_store)

        logger.info(
            "Available Atlas tools: %s",
            self.tools.available(),
        )

        # --------------------------------------------------
        # Thread
        # --------------------------------------------------

        self.thread = QThread(self)

        # --------------------------------------------------
        # Worker
        # --------------------------------------------------

        self.worker = AIWorker(
            tools=self.tools
        )

        self.worker.moveToThread(
            self.thread
        )

        # --------------------------------------------------
        # Controller -> Worker
        # --------------------------------------------------

        self.generate_requested.connect(
            self.worker.process
        )

        self.coding_requested.connect(
            self.worker.process_coding
        )

        # --------------------------------------------------
        # Worker -> Service
        # --------------------------------------------------

        self.worker.chunk.connect(
            self._handle_chunk
        )

        self.worker.finished.connect(
            self._handle_finished
        )

        self.worker.error.connect(
            self._handle_error
        )

        self.worker.coding_result.connect(
            self.coding_result.emit
        )

        self.worker.coding_error.connect(
            self.coding_error.emit
        )

        self.worker.coding_finished.connect(
            self.coding_finished.emit
        )

        # --------------------------------------------------
        # Runtime state
        # --------------------------------------------------

        self._running = False
        self._stopping = False

        logger.info(
            "AIService initialized."
        )

    # ======================================================
    # START
    # ======================================================

    def start(self):

        if self.thread.isRunning():

            logger.info(
                "AI thread already running."
            )

            self._running = True

            return

        self._stopping = False

        self.thread.start()

        self._running = True

        logger.info(
            "AI Thread started."
        )

    # ======================================================
    # STOP
    # ======================================================

    def stop(self):

        if not self.thread.isRunning():

            self._running = False

            return

        self._stopping = True

        logger.info(
            "Stopping AI Thread..."
        )

        self.thread.quit()

        self.thread.wait()

        self._running = False

        logger.info(
            "AI Thread stopped."
        )

    # ======================================================
    # CANCEL CURRENT GENERATION
    # ======================================================

    def cancel_generation(self):
        """Request cancellation without killing the worker thread."""
        self._stopping = True
        try:
            self.worker.request_stop()
        except Exception:
            logger.exception("Failed to request AI generation stop")

    # ======================================================
    # GENERATE
    # ======================================================

    def generate(
        self,
        message,
        generation_id="",
    ):

        message = str(
            message
        ).strip()

        if not message:

            logger.warning(
                "AIService.generate() received empty message."
            )

            return

        # --------------------------------------------------
        # Make sure worker is running
        # --------------------------------------------------

        if not self.thread.isRunning():

            logger.warning(
                "AI thread is not running. Starting it."
            )

            self.start()

        self._stopping = False
        gen_id = str(generation_id or "")

        logger.info(
            "Sending message to AI worker (generation_id=%s).",
            gen_id,
        )

        # --------------------------------------------------
        # Send request to worker thread
        # --------------------------------------------------

        self.generate_requested.emit(
            message,
            gen_id,
        )

    # ======================================================
    # CODING AGENT
    # ======================================================

    def execute_coding(
        self,
        task,
        permissions,
        max_attempts=2,
    ):
        """Execute an approved Coding Agent task on the worker thread."""

        task = str(
            task or ""
        ).strip()

        if not task:
            logger.warning(
                "AIService.execute_coding() received empty task."
            )
            return

        if not self.thread.isRunning():
            logger.warning(
                "AI thread is not running. Starting it."
            )
            self.start()

        self._stopping = False

        logger.info(
            "Sending coding task to AI worker."
        )

        self.coding_requested.emit(
            task,
            permissions,
            int(max_attempts),
        )

    # ======================================================
    # WORKER CHUNK
    # ======================================================

    def _handle_chunk(
        self,
        text,
        generation_id="",
    ):

        if text is None:

            return

        text = str(
            text
        )

        if not text:

            return

        logger.info(
            "AI response received."
        )

        # --------------------------------------------------
        # ONLY emit Qt signal.
        #
        # Do NOT publish ChunkReceived here.
        #
        # Controller owns EventBus routing.
        # --------------------------------------------------

        self.chunk_ready.emit(
            text,
            str(generation_id or ""),
        )

    # ======================================================
    # WORKER FINISHED
    # ======================================================

    def _handle_finished(
        self,
        generation_id="",
    ):

        logger.info(
            "AI generation finished."
        )

        # --------------------------------------------------
        # ONLY emit Qt signal.
        #
        # Do not publish ThinkingFinished here.
        # Controller handles EventBus state.
        # --------------------------------------------------

        self.finished.emit(
            str(generation_id or "")
        )

    # ======================================================
    # WORKER ERROR
    # ======================================================

    def _handle_error(
        self,
        message,
        generation_id="",
    ):

        message = str(
            message
        )

        logger.error(
            "AI generation error: %s",
            message,
        )

        # --------------------------------------------------
        # ONLY emit Qt signal.
        # --------------------------------------------------

        self.error.emit(
            message,
            str(generation_id or ""),
        )
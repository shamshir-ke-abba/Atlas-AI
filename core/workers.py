# core/workers.py

import logging

from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
)

from ai.brain import AtlasBrain
from ai.model import AtlasModel
from core.tool_manager import ToolManager


logger = logging.getLogger("atlas")


class AIWorker(QObject):
    """
    Worker responsible for Atlas AI processing.

    Architecture:

        Message
           ↓
        AtlasBrain
           ↓
        ToolManager
        ├── Plugins
        └── Qwen fallback

    Tools are initialized here and injected into AtlasBrain.
    """

    # =========================================================
    # SIGNALS
    # =========================================================

    chunk = Signal(str)

    error = Signal(str)

    finished = Signal()

    tool_chunk = Signal(str)

    tool_finished = Signal()

    tool_error = Signal(str)

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self):

        super().__init__()

        # -----------------------------------------------------
        # Conversation
        # -----------------------------------------------------

        self.conversation_id = None
        self.conversation_history = []

        # -----------------------------------------------------
        # Atlas model
        # -----------------------------------------------------

        self.model = AtlasModel()

        # -----------------------------------------------------
        # Tool system
        # -----------------------------------------------------

        self.tools = ToolManager()

        logger.info(
            "Available Atlas tools: %s",
            self.tools.available(),
        )

        # -----------------------------------------------------
        # Atlas brain
        # -----------------------------------------------------

        self.brain = AtlasBrain(
            model=self.model,
            memory=None,
            tools=self.tools,
        )

        logger.info(
            "AIWorker initialized with tool system"
        )

    # =========================================================
    # CONVERSATION
    # =========================================================

    def set_conversation(
        self,
        conversation_id,
        history=None,
    ):
        """
        Set the active conversation and its history.
        """

        self.conversation_id = conversation_id

        self.conversation_history = list(
            history or []
        )

        self.brain.set_conversation_history(
            self.conversation_history
        )

    # ---------------------------------------------------------

    def clear_conversation(self):
        """
        Clear current conversation context.
        """

        self.conversation_id = None

        self.conversation_history = []

        try:

            self.brain.set_conversation_history(
                []
            )

        except Exception:

            logger.exception(
                "Failed to clear brain conversation"
            )

    # =========================================================
    # SYNCHRONOUS PROCESSING
    # =========================================================

    def process_sync(
        self,
        message: str,
        conversation_history=None,
    ) -> str:
        """
        Process a message synchronously.

        Controller uses this path.

        AtlasBrain decides whether the request goes to:
            - a deterministic plugin/tool
            - or Qwen
        """

        try:

            if conversation_history is not None:

                self.conversation_history = list(
                    conversation_history
                )

                self.brain.set_conversation_history(
                    self.conversation_history
                )

            logger.info(
                "Processing message: %s",
                message,
            )

            response = self.brain.process_message(
                message
            )

            if response is None:
                return ""

            return str(response)

        except Exception as exc:

            logger.exception(
                "Synchronous AI processing failed"
            )

            return f"Error: {exc}"

    # =========================================================
    # NORMAL ASYNC AI
    # =========================================================

    @Slot(str)
    def process(
        self,
        message: str,
    ):
        """
        Process a normal AI request asynchronously.
        """

        try:

            response = self.process_sync(
                message,
                self.conversation_history,
            )

            if response:

                self.chunk.emit(
                    response
                )

        except Exception as exc:

            logger.exception(
                "Async AI processing failed"
            )

            self.error.emit(
                str(exc)
            )

        finally:

            self.finished.emit()

    # =========================================================
    # TOOL AI
    # =========================================================

    @Slot(str)
    def process_tool(
        self,
        message: str,
    ):
        """
        Process a lightweight AI request for a tool.

        This intentionally bypasses AtlasBrain.
        It is used only when a tool specifically needs
        a small LLM-generated response.
        """

        try:

            for piece in self.model.generate(
                message,
                stream=True,
            ):

                if piece:

                    self.tool_chunk.emit(
                        str(piece)
                    )

        except Exception as exc:

            logger.exception(
                "Tool AI processing failed"
            )

            self.tool_error.emit(
                str(exc)
            )

        finally:

            self.tool_finished.emit()
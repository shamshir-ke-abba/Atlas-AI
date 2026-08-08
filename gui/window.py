"""
gui/window.py

Main Atlas Window.
"""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QWidget,
)

from gui.widgets.sidebar import AtlasSidebar
from gui.widgets.chat import AtlasChat
from gui.widgets.statusbar import AtlasStatusBar


class AtlasWindow(QMainWindow):

    def __init__(
        self,
        bus,
        state,
        controller=None,
    ):

        super().__init__()

        self.bus = bus
        self.state = state
        self.controller = controller

        self.setup_window()
        self.build_ui()

    # =====================================================
    # Window
    # =====================================================

    def setup_window(self):

        self.setWindowTitle(
            "Atlas AI"
        )

        self.resize(
            1400,
            900
        )

        self.setMinimumSize(
            1100,
            700
        )

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        root = QWidget()

        self.setCentralWidget(
            root
        )

        layout = QHBoxLayout(
            root
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(
            0
        )

        # ---------------------------------
        # Sidebar
        # ---------------------------------

        self.sidebar = AtlasSidebar(
            self.bus
        )

        self.sidebar.setMinimumWidth(
            240
        )

        # ---------------------------------
        # Chat
        # ---------------------------------

        self.chat = AtlasChat(
            self.bus
        )

        self.chat.add_message(
            "Atlas",
            "Hello Saad, systems online."
        )

        # ---------------------------------
        # Status
        # ---------------------------------

        self.status = AtlasStatusBar(
            self.bus
        )

        self.status.setMinimumWidth(
            260
        )

        # ---------------------------------
        # Layout
        # ---------------------------------

        layout.addWidget(
            self.sidebar
        )

        layout.addWidget(
            self.chat,
            1
        )

        # ---------------------------------
        # Controller
        # ---------------------------------

        if self.controller is not None:

            self.sidebar.set_controller(
                self.controller
            )

        # ---------------------------------
        # Conversation Selection
        # ---------------------------------

        self.sidebar.conversation_selected.connect(
            self.handle_conversation_selected
        )

    # =====================================================
    # Conversation Selection
    # =====================================================

    def handle_conversation_selected(
        self,
        conversation_id,
    ):

        if self.controller is None:
            return

        success = self.controller.load_conversation(
            conversation_id
        )

        if not success:
            return

        self.chat.load_conversation(
            self.controller.ai.worker.brain.conversation
        )
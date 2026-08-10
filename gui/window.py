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
        controller,
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
            900,
        )

        self.setMinimumSize(
            1100,
            700,
        )

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        root = QWidget()

        root.setObjectName(
            "AtlasWindow"
        )

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
            0,
        )

        layout.setSpacing(
            0
        )

        # ---------------------------------
        # Sidebar
        # ---------------------------------

        self.sidebar = AtlasSidebar(
            bus=self.bus,
            controller=self.controller,
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
        # Conversation Synchronization
        # ---------------------------------

        self.sidebar.conversation_loaded.connect(
            self.handle_conversation_loaded
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
            1,
        )

    # =====================================================
    # Conversation UI
    # =====================================================

    def handle_conversation_loaded(
        self,
        conversation,
    ):

        # ---------------------------------
        # New Chat / Empty Conversation
        # ---------------------------------

        if conversation is None:

            self.chat.clear_messages()

            self.chat.add_message(
                "Atlas",
                "Hello Saad, systems online."
            )

            return

        # ---------------------------------
        # Existing Conversation
        # ---------------------------------

        self.chat.load_conversation(
            conversation
        )

    # =====================================================
    # History
    # =====================================================

    def refresh_history(self):

        self.sidebar.refresh_history()
"""
gui/window.py

Main Atlas Window.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QWidget,
)

from gui.theme import *
from gui.widgets.sidebar import AtlasSidebar
from gui.widgets.chat import AtlasChat
from gui.widgets.statusbar import AtlasStatusBar



class AtlasWindow(QMainWindow):

    def __init__(self, bus, state):

        super().__init__()

        self.bus = bus
        self.state = state

        self.setup_window()
        self.build_ui()

    # =====================================================
    # Window
    # =====================================================

    def setup_window(self):

        self.setWindowTitle("Atlas AI")

        self.resize(1400, 900)

        self.setMinimumSize(1100, 700)

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        root = QWidget()

        self.setCentralWidget(root)

        layout = QHBoxLayout(root)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(0)

        # ---------------------------------
        # Sidebar
        # ---------------------------------

        sidebar = AtlasSidebar(
            self.bus
        )

        sidebar.setMinimumWidth(240)

        # ---------------------------------
        # Chat Placeholder
        # ---------------------------------

        chat = AtlasChat(
            self.bus
        )

        chat.add_message(
            "Atlas",
            "Hello Saad , systems online."
        )
        
        # ---------------------------------
        # Status Placeholder
        # ---------------------------------

        status = AtlasStatusBar(
            self.bus
        )

        status.setMinimumWidth(260)

        layout.addWidget(sidebar)

        layout.addWidget(chat, 1)

        layout.addWidget(status)
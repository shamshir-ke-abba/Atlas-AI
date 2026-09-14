"""
Atlas V3 Main Window.
"""

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from gui.widgets.chat import AtlasChat
from gui.widgets.sidebar import AtlasSidebar
from gui.widgets.statusbar import AtlasStatusBar
from gui.widgets.tool_workspace import ToolWorkspace


class AtlasWindow(QMainWindow):
    def __init__(self, bus, state, controller):
        super().__init__()
        self.bus = bus
        self.state = state
        self.controller = controller

        self.setWindowTitle("Atlas AI")
        icon_path = Path(__file__).resolve().parents[1] / "assets" / "atlas_favicon.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1400, 900)
        self.setMinimumSize(1000, 650)

        self.build_ui()

        # Use the available desktop instead of wasting space in a small
        # floating window. Keep normal window decorations for easy access.
        QTimer.singleShot(0, self.showMaximized)

    def build_ui(self):
        root = QWidget(self)
        root.setObjectName("AtlasWindow")
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = AtlasSidebar(
            bus=self.bus,
            controller=self.controller,
        )
        self.sidebar.setMinimumWidth(260)
        self.sidebar.setMaximumWidth(260)

        self.chat = AtlasChat(
            self.bus,
            controller=self.controller,
        )

        self.tool_workspace = ToolWorkspace(
            controller=self.controller,
        )

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.chat)
        self.content_stack.addWidget(self.tool_workspace)
        self.content_stack.setCurrentWidget(self.chat)

        self.status = AtlasStatusBar(
            self.bus,
            controller=self.controller,
            state=self.state,
        )
        self.status.setMinimumWidth(280)
        self.status.setMaximumWidth(280)

        self.sidebar.conversation_loaded.connect(
            self.handle_conversation_loaded
        )
        self.sidebar.tools_requested.connect(
            self.show_tools
        )

        layout.addWidget(self.sidebar)
        layout.addWidget(self.content_stack, 1)
        layout.addWidget(self.status)

    def handle_conversation_loaded(self, conversation):
        self.show_chat()
        self.chat.load_conversation(conversation)

    def show_chat(self):
        self.content_stack.setCurrentWidget(self.chat)

    def show_tools(self):
        self.tool_workspace.show_overview()
        self.content_stack.setCurrentWidget(self.tool_workspace)

    def refresh_history(self):
        self.sidebar.refresh_history()

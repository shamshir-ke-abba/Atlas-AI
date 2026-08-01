"""
gui/widgets/sidebar.py

Atlas Sidebar Widget.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
)

from core.events import (
    ConversationCleared,
)


class AtlasSidebar(QWidget):

    def __init__(
        self,
        bus,
        parent=None,
    ):

        super().__init__(parent)

        self.bus = bus

        self.setObjectName("Sidebar")

        self.build_ui()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        title = QLabel(
            "Atlas AI"
        )

        title.setObjectName(
            "SidebarTitle"
        )

        layout.addWidget(
            title
        )

        self.new_chat_button = QPushButton(
            "New Chat"
        )

        self.new_chat_button.clicked.connect(
            self.handle_new_chat
        )

        layout.addWidget(
            self.new_chat_button
        )

        layout.addStretch()

    # =====================================================
    # Events
    # =====================================================

    def handle_new_chat(
        self,
    ):

        self.bus.publish(
            ConversationCleared()
        )
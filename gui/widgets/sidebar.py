"""
gui/widgets/sidebar.py

Atlas Sidebar Widget.
"""

from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
)

from core.events import ConversationCleared


class AtlasSidebar(QWidget):

    conversation_selected = Signal(str)

    def __init__(
        self,
        bus,
        parent=None,
    ):

        super().__init__(parent)

        self.bus = bus
        self.controller = None

        self.setObjectName(
            "Sidebar"
        )

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

        layout.setSpacing(
            10
        )

        # ---------------------------------
        # Title
        # ---------------------------------

        title = QLabel(
            "Atlas AI"
        )

        title.setObjectName(
            "SidebarTitle"
        )

        layout.addWidget(
            title
        )

        # ---------------------------------
        # New Chat
        # ---------------------------------

        self.new_chat_button = QPushButton(
            "+ New Chat"
        )

        self.new_chat_button.clicked.connect(
            self.handle_new_chat
        )

        layout.addWidget(
            self.new_chat_button
        )

        # ---------------------------------
        # Workspaces
        # ---------------------------------

        self.chat_button = QPushButton(
            "Chat"
        )

        self.tools_button = QPushButton(
            "Tools"
        )

        self.web_button = QPushButton(
            "Web"
        )

        self.study_button = QPushButton(
            "Study"
        )

        layout.addWidget(
            self.chat_button
        )

        layout.addWidget(
            self.tools_button
        )

        layout.addWidget(
            self.web_button
        )

        layout.addWidget(
            self.study_button
        )

        # ---------------------------------
        # History Label
        # ---------------------------------

        history_title = QLabel(
            "CHAT HISTORY"
        )

        history_title.setObjectName(
            "HistoryTitle"
        )

        layout.addWidget(
            history_title
        )

        # ---------------------------------
        # History Scroll Area
        # ---------------------------------

        self.history_container = QWidget()

        self.history_layout = QVBoxLayout(
            self.history_container
        )

        self.history_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.history_layout.setSpacing(
            5
        )

        self.history_layout.addStretch()

        self.history_scroll = QScrollArea()

        self.history_scroll.setWidgetResizable(
            True
        )

        self.history_scroll.setWidget(
            self.history_container
        )

        layout.addWidget(
            self.history_scroll,
            1,
        )

    # =====================================================
    # Controller
    # =====================================================

    def set_controller(
        self,
        controller,
    ):

        self.controller = controller

        self.refresh_history()

    # =====================================================
    # History
    # =====================================================

    def refresh_history(self):

        if self.controller is None:
            return

        # ---------------------------------
        # Remove existing buttons
        # ---------------------------------

        while self.history_layout.count() > 1:

            item = self.history_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()

        # ---------------------------------
        # Load conversations
        # ---------------------------------

        conversations = (
            self.controller.list_conversations()
        )

        for conversation in conversations:

            conversation_id = conversation.get(
                "id"
            )

            title = conversation.get(
                "title",
                "New Chat",
            )

            button = QPushButton(
                title
            )

            button.setObjectName(
                "HistoryButton"
            )

            button.setToolTip(
                title
            )

            button.clicked.connect(
                lambda checked=False,
                cid=conversation_id:
                self.handle_conversation_selected(
                    cid
                )
            )

            self.history_layout.insertWidget(
                self.history_layout.count() - 1,
                button,
            )

    # =====================================================
    # Events
    # =====================================================

    def handle_new_chat(
        self,
    ):

        self.bus.publish(
            ConversationCleared()
        )

        self.refresh_history()

    def handle_conversation_selected(
        self,
        conversation_id,
    ):

        self.conversation_selected.emit(
            conversation_id
        )
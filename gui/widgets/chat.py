"""
gui/widgets/chat.py

Atlas Chat Widget.
"""

from core.events import (
    ChunkReceived,
    MessageReceived,
)

from PySide6.QtWidgets import (
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.widgets.inputbar import AtlasInputBar
from gui.widgets.message import AtlasMessage


class AtlasChat(QWidget):

    def __init__(
        self,
        bus,
        parent=None,
    ):

        super().__init__(parent)

        self.bus = bus

        self.current_ai_message = None

        self.bus.subscribe(
            ChunkReceived,
            self.handle_response,
        )

        self.setObjectName(
            "Chat"
        )

        self.build_ui()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        layout.setSpacing(
            10
        )

        # -----------------------------
        # Header
        # -----------------------------

        title = QLabel(
            "Chat Area"
        )

        title.setObjectName(
            "ChatTitle"
        )

        layout.addWidget(
            title
        )

        # -----------------------------
        # Messages Area
        # -----------------------------

        self.messages = QWidget()

        self.messages_layout = QVBoxLayout(
            self.messages
        )

        self.messages_layout.setSpacing(
            10
        )

        self.messages_layout.addStretch()

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(
            True
        )

        self.scroll.setWidget(
            self.messages
        )

        layout.addWidget(
            self.scroll,
            1,
        )

        # -----------------------------
        # Input
        # -----------------------------

        self.input_bar = AtlasInputBar()

        self.input_bar.message_sent.connect(
            self.handle_message
        )

        layout.addWidget(
            self.input_bar
        )

    # =====================================================
    # Messages
    # =====================================================

    def add_message(
        self,
        sender,
        text,
    ):

        message = AtlasMessage(
            sender,
            text,
        )

        self.messages_layout.insertWidget(
            self.messages_layout.count() - 1,
            message,
        )

        return message

    # =====================================================
    # Clear Messages
    # =====================================================

    def clear_messages(self):

        while self.messages_layout.count() > 1:

            item = self.messages_layout.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()

        self.current_ai_message = None

    # =====================================================
    # Load Conversation
    # =====================================================

    def load_conversation(
        self,
        conversation,
    ):

        self.clear_messages()

        for message in conversation.history():

            role = message.get(
                "role"
            )

            text = message.get(
                "content",
                "",
            )

            if role == "user":

                sender = "User"

            else:

                sender = "Atlas"

            self.add_message(
                sender,
                text,
            )

        self.scroll_to_bottom()

    # =====================================================
    # Input Handling
    # =====================================================

    def handle_message(
        self,
        text,
    ):

        self.current_ai_message = None

        self.add_message(
            "User",
            text,
        )

        self.bus.publish(
            MessageReceived(
                text
            )
        )

    # =====================================================
    # AI Response Handling
    # =====================================================

    def handle_response(
        self,
        event,
    ):

        if self.current_ai_message is None:

            self.current_ai_message = self.add_message(
                "Atlas",
                event.text,
            )

        else:

            self.current_ai_message.set_text(
                self.current_ai_message.text
                + event.text
            )

        self.scroll_to_bottom()

    # =====================================================
    # Scrolling
    # =====================================================

    def scroll_to_bottom(self):

        scrollbar = (
            self.scroll.verticalScrollBar()
        )

        scrollbar.setValue(
            scrollbar.maximum()
        )
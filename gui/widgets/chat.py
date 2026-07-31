"""
gui/widgets/chat.py

Atlas Chat Widget.
"""

from core.events import (
    MessageReceived,
    ChunkReceived,
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
            parent=None
            ):

        super().__init__(parent)

        self.bus = bus

        self.bus.subscribe(
            ChunkReceived,
            self.handle_response
        )
     
        self.setObjectName("Chat")

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
            20
        )

        layout.setSpacing(10)


        # -----------------------------
        # Header
        # -----------------------------

        title = QLabel("Chat Area")

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

        self.messages_layout.addStretch()


        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setWidget(
            self.messages
        )

        layout.addWidget(
            scroll,
            1
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
        text
    ):

        message = AtlasMessage(
            sender,
            text
        )

        self.messages_layout.insertWidget(
            self.messages_layout.count() - 1,
            message
        )

        
    # =====================================================
    # Input Handling
    # =====================================================

    def handle_message(
    self,
    text
):

        self.add_message(
        "User",
        text
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
        event
    ):

        self.add_message(
            "Atlas",
            event.text
        )
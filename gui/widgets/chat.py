"""
gui/widgets/chat.py

Atlas Chat Widget.
"""

from PySide6.QtCore import QTimer

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

        # =================================================
        # Current AI Response
        # =================================================

        self.current_ai_message = None

        self.current_ai_response = ""

        # =================================================
        # Thinking Animation
        # =================================================

        self.thinking_frame = 0

        self.thinking_timer = QTimer(self)

        # Slower, calmer animation
        self.thinking_timer.setInterval(
            220
        )

        self.thinking_timer.timeout.connect(
            self.animate_thinking
        )

        # =================================================
        # Events
        # =================================================

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
            10,
        )

        # ---------------------------------
        # Header
        # ---------------------------------

        title = QLabel(
            "Chat Area"
        )

        title.setObjectName(
            "ChatTitle"
        )

        layout.addWidget(
            title
        )

        # ---------------------------------
        # Messages Area
        # ---------------------------------

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

        # ---------------------------------
        # Input
        # ---------------------------------

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

        self.stop_thinking_animation()

        while self.messages_layout.count() > 1:

            item = self.messages_layout.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()

        self.current_ai_message = None

        self.current_ai_response = ""

    # =====================================================
    # Load Conversation
    # =====================================================

    def load_conversation(
        self,
        conversation,
    ):

        self.stop_thinking_animation()

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

        # ---------------------------------
        # Stop previous animation
        # ---------------------------------

        self.stop_thinking_animation()

        self.current_ai_message = None

        self.current_ai_response = ""

        # ---------------------------------
        # User message
        # ---------------------------------

        self.add_message(
            "User",
            text,
        )

        # ---------------------------------
        # Temporary Atlas thinking message
        # ---------------------------------

        self.current_ai_message = self.add_message(
            "Atlas",
            "· · ·",
        )

        self.current_ai_message.set_thinking(
            True
        )

        self.thinking_frame = 0

        self.thinking_timer.start()

        self.scroll_to_bottom()

        # ---------------------------------
        # Send to backend
        # ---------------------------------

        self.bus.publish(
            MessageReceived(
                text
            )
        )

    # =====================================================
    # Thinking Animation
    # =====================================================

    def animate_thinking(self):

        if self.current_ai_message is None:

            self.stop_thinking_animation()

            return

        # -------------------------------------------------
        # Smooth slow pulse
        #
        # Empty
        # ↓
        # 1 dot
        # ↓
        # 2 dots
        # ↓
        # 3 dots
        # ↓
        # 2 dots
        # ↓
        # 1 dot
        # ↓
        # Empty
        #
        # Then repeat.
        # -------------------------------------------------

        frames = (
                  "● · ·",
                  "● ● ·",
                  "● ● ●",
                  "· ● ●",
                  "· · ●",
                  "· ● ●",
                  "● ● ●",
                  "● ● ·",
                  "● · ·",
                  "· · ·",
                 )

        frame = frames[
            self.thinking_frame
            % len(frames)
        ]

        self.current_ai_message.set_text(
            frame
        )

        self.thinking_frame += 1

        self.scroll_to_bottom()

    # =====================================================
    # Stop Thinking Animation
    # =====================================================

    def stop_thinking_animation(self):

        if self.thinking_timer.isActive():

            self.thinking_timer.stop()

        self.thinking_frame = 0

    # =====================================================
    # AI Response Handling
    # =====================================================

    def handle_response(
        self,
        event,
    ):

        # ---------------------------------
        # Safety
        # ---------------------------------

        if self.current_ai_message is None:

            self.current_ai_message = self.add_message(
                "Atlas",
                "",
            )

            self.current_ai_response = ""

        # ---------------------------------
        # Stop thinking animation
        # ---------------------------------

        if self.thinking_timer.isActive():

            self.stop_thinking_animation()

            self.current_ai_message.set_thinking(
                False
            )

        # ---------------------------------
        # Accumulate response
        #
        # IMPORTANT:
        # Never replace the previous chunk.
        # ---------------------------------

        self.current_ai_response += event.text

        # ---------------------------------
        # Display accumulated response
        # ---------------------------------

        self.current_ai_message.set_text(
            self.current_ai_response
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
"""
gui/widgets/message.py

Atlas Chat Message Widget.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)


class AtlasMessage(QWidget):

    def __init__(
        self,
        sender,
        text,
        parent=None,
    ):

        super().__init__(parent)

        self.sender = sender
        self.text = text

        self.setObjectName(
            "Message"
        )

        self.build_ui()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        main_layout = QHBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            12,
            8,
            12,
            8,
        )

        main_layout.setSpacing(
            12
        )

        # ---------------------------------
        # Content
        # ---------------------------------

        content_layout = QVBoxLayout()

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(
            4
        )

        # ---------------------------------
        # Sender
        # ---------------------------------

        self.sender_label = QLabel(
            self.sender
        )

        self.sender_label.setObjectName(
            "MessageSender"
        )

        content_layout.addWidget(
            self.sender_label
        )

        # ---------------------------------
        # Message
        # ---------------------------------

        self.message_label = QLabel(
            self.text
        )

        self.message_label.setWordWrap(
            True
        )

        self.message_label.setObjectName(
            "MessageText"
        )

        content_layout.addWidget(
            self.message_label
        )

        # ---------------------------------
        # Layout
        # ---------------------------------

        main_layout.addLayout(
            content_layout,
            1,
        )

    # =====================================================
    # Public API
    # =====================================================

    def set_text(
        self,
        text,
    ):

        self.text = text

        self.message_label.setText(
            text
        )

    # =====================================================
    # Thinking Indicator
    # =====================================================

    def set_thinking(
        self,
        thinking=True,
    ):

        if thinking:

            self.message_label.setText(
                "● ● ●"
            )

        else:

            self.message_label.setText(
                self.text
            )
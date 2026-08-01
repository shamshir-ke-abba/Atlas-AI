"""
gui/widgets/message.py

Atlas Chat Message Widget.
"""

from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)


class AtlasMessage(QWidget):

    def __init__(
        self,
        sender,
        text,
        parent=None
    ):

        super().__init__(parent)

        self.sender = sender
        self.text = text

        self.setObjectName("Message")

        self.build_ui()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            12,
            8,
            12,
            8
        )

        self.sender_label = QLabel(
            self.sender
        )

        self.sender_label.setObjectName(
            "MessageSender"
        )

        layout.addWidget(
            self.sender_label
        )

        self.message_label = QLabel(
            self.text
        )

        self.message_label.setWordWrap(
            True
        )

        self.message_label.setObjectName(
            "MessageText"
        )

        layout.addWidget(
            self.message_label
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
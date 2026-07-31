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

        sender_label = QLabel(
            self.sender
        )

        sender_label.setObjectName(
            "MessageSender"
        )

        layout.addWidget(
            sender_label
        )


        message_label = QLabel(
            self.text
        )

        message_label.setWordWrap(
            True
        )

        message_label.setObjectName(
            "MessageText"
        )

        layout.addWidget(
            message_label
        )
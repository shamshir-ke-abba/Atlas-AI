"""
gui/widgets/inputbar.py

Atlas Input Bar Widget.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QWidget,
)


class AtlasInputBar(QWidget):

    message_sent = Signal(str)


    def __init__(self, parent=None):

        super().__init__(parent)

        self.setObjectName("InputBar")

        self.build_ui()

        self.connect_events()


    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            10,
            10,
            10,
            10
        )


        self.input_field = QLineEdit()

        self.input_field.setPlaceholderText(
            "Ask Atlas something..."
        )

        self.input_field.setObjectName(
            "InputField"
        )


        self.send_button = QPushButton(
            "Send"
        )

        self.send_button.setObjectName(
            "SendButton"
        )


        layout.addWidget(
            self.input_field,
            1
        )

        layout.addWidget(
            self.send_button
        )


    # =====================================================
    # Events
    # =====================================================

    def connect_events(self):

        self.send_button.clicked.connect(
            self.send_message
        )

        self.input_field.returnPressed.connect(
            self.send_message
        )


    def send_message(self):

        text = self.input_field.text().strip()

        if not text:
            return

        self.message_sent.emit(
            text
        )

        self.input_field.clear()
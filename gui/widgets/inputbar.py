"""Atlas V3 chat input with an inline generation stop control."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget


class AtlasInputBar(QWidget):
    message_sent = Signal(str)
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InputBar")
        self._generating = False
        self.build_ui()
        self.connect_events()

    def build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 18)
        layout.setSpacing(10)

        self.input_field = QLineEdit()
        self.input_field.setObjectName("InputField")
        self.input_field.setPlaceholderText("Message Atlas...")
        self.input_field.setMinimumHeight(44)

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("SendButton")
        self.send_button.setMinimumHeight(44)
        self.send_button.setMinimumWidth(80)
        self.send_button.setToolTip("Send message")

        layout.addWidget(self.input_field, 1)
        layout.addWidget(self.send_button)

    def connect_events(self):
        self.send_button.clicked.connect(self._button_clicked)
        self.input_field.returnPressed.connect(self.send_message)

    def _button_clicked(self):
        if self._generating:
            self.stop_requested.emit()
        else:
            self.send_message()

    def send_message(self):
        if self._generating:
            return
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self.message_sent.emit(text)

    def set_generating(self, generating):
        self._generating = bool(generating)
        if self._generating:
            self.send_button.setText("■")
            self.send_button.setToolTip("Stop generation")
            self.send_button.setEnabled(True)
            self.input_field.setEnabled(False)
        else:
            self.send_button.setText("Send")
            self.send_button.setToolTip("Send message")
            self.send_button.setEnabled(True)
            self.input_field.setEnabled(True)

"""
Atlas V3 useful status panel with distinct state indicators.
"""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from core.events import ThinkingStarted, ThinkingFinished, ErrorOccurred


class AtlasStatusBar(QWidget):
    def __init__(self, bus, controller=None, state=None, parent=None):
        super().__init__(parent)
        self.bus = bus
        self.controller = controller
        self.state = state
        self.setObjectName("StatusBar")

        self.bus.subscribe(ThinkingStarted, self.thinking_started)
        self.bus.subscribe(ThinkingFinished, self.thinking_finished)
        self.bus.subscribe(ErrorOccurred, self.error_state)

        self.build_ui()

        self.timer = QTimer(self)
        self.timer.setInterval(1200)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 22, 18, 22)
        layout.setSpacing(10)

        title = QLabel("Atlas Status")
        title.setObjectName("StatusTitle")
        layout.addWidget(title)

        self.state_card = self._card("STATE", "●  Ready")
        self.model_card = self._card("MODEL", "Local model")
        self.tools_card = self._card("TOOLS", "Loading...")
        self.chat_card = self._card("CONVERSATION", "No active chat")
        self.runtime_card = self._card("RUNTIME", "Atlas online")

        for card in (
            self.state_card,
            self.model_card,
            self.tools_card,
            self.chat_card,
            self.runtime_card,
        ):
            layout.addWidget(card)

        layout.addStretch(1)

        footer = QLabel("Local • Event-driven • Modular")
        footer.setObjectName("StatusFooter")
        footer.setWordWrap(True)
        layout.addWidget(footer)

    def _card(self, heading, value):
        card = QFrame()
        card.setObjectName("StatusCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)

        title = QLabel(heading)
        title.setObjectName("StatusCardTitle")
        layout.addWidget(title)

        label = QLabel(value)
        label.setObjectName("StatusCardValue")
        label.setWordWrap(True)
        layout.addWidget(label)

        card.value_label = label
        return card

    def _set_state(self, text, kind):
        label = self.state_card.value_label
        label.setText(text)
        label.setStyleSheet(
            {
                "ready": "color:#55d66b; font-weight:600;",
                "thinking": "color:#f2c94c; font-weight:600;",
                "error": "color:#ff5f56; font-weight:600;",
            }.get(kind, "")
        )

    def refresh(self):
        generating = bool(
            getattr(self.state, "is_generating", False)
        ) if self.state is not None else False

        self._set_state(
            "●  Thinking" if generating else "●  Ready",
            "thinking" if generating else "ready",
        )

        try:
            from config import MODEL_NAME
            self.model_card.value_label.setText(str(MODEL_NAME))
        except Exception:
            self.model_card.value_label.setText("Local model")

        try:
            manager = getattr(
                getattr(self.controller, "ai", None),
                "tools",
                None,
            )
            if manager is not None:
                info = manager.status()
                self.tools_card.value_label.setText(
                    f"{info.get('enabled', 0)} enabled / "
                    f"{info.get('total', 0)} total"
                )
        except Exception:
            pass

        try:
            conversation = self.controller.get_active_conversation()
            title = getattr(conversation, "title", None)
            self.chat_card.value_label.setText(
                str(title or "Active chat")
            )
        except Exception:
            self.chat_card.value_label.setText("No active chat")

        self.runtime_card.value_label.setText("Atlas online")

    def thinking_started(self, event):
        self._set_state("●  Thinking", "thinking")

    def thinking_finished(self, event):
        self._set_state("●  Ready", "ready")

    def error_state(self, event):
        self._set_state("●  Error", "error")

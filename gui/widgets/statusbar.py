"""Atlas V3 status and context panel with semantic state indicators and Arcade.

Conforms to docs/design/ATLAS_DESIGN_SYSTEM_V1.md.
Communicates application and runtime state quietly and clearly.
Houses compact Tools entry and the Atlas Arcade entry.
"""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.events import (
    ChunkReceived,
    ErrorOccurred,
    ThinkingFinished,
    ThinkingStarted,
    ToolFinished,
    ToolRequested,
)
from gui.widgets.arcade import (
    AtlasArcadeCard,
    STATE_ARCADE_CLOSED,
    STATE_ARCADE_SELECTOR,
    STATE_GAME_PLAYING,
)
from gui.widgets.snake import AtlasSnakeCard


class AtlasStatusBar(QWidget):
    tools_requested = Signal()

    STATE_COLORS = {
        "ready": "#4ADE80",       # semantic success
        "idle": "#82828C",        # muted text
        "thinking": "#4FB8BA",    # brand text
        "generating": "#4FB8BA",  # brand text
        "responding": "#4FB8BA",  # brand text
        "tool": "#60A5FA",        # semantic info
        "searching": "#60A5FA",   # semantic info
        "success": "#4ADE80",     # semantic success
        "error": "#F87171",       # semantic error
        "offline": "#82828C",     # muted text
    }

    def __init__(self, bus, controller=None, state=None, parent=None):
        super().__init__(parent)
        self.bus = bus
        self.controller = controller
        self.state = state
        self._current_state = "ready"
        self._current_label = "Ready"
        self._start_time = time.time()
        self.setObjectName("StatusBar")

        if self.bus is not None:
            self.bus.subscribe(ThinkingStarted, self.thinking_started)
            self.bus.subscribe(ThinkingFinished, self.thinking_finished)
            self.bus.subscribe(ChunkReceived, self.chunk_received)
            self.bus.subscribe(ToolRequested, self.tool_requested)
            self.bus.subscribe(ToolFinished, self.tool_finished)
            self.bus.subscribe(ErrorOccurred, self.error_state)

        self.build_ui()

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)

        title = QLabel("ATLAS STATUS")
        title.setObjectName("StatusTitle")
        layout.addWidget(title)

        self.state_card = self._card("CURRENT STATE", "Ready")
        self.model_card = self._card("MODEL", "Local model")
        self.activity_card = self._card("ACTIVITY", "Idle")
        self.tools_card = self.activity_card  # backward-compatible alias
        self.chat_card = self._card("SESSION", "No active chat")
        self.runtime_card = self._card("SYSTEM", "Online")

        for card in (
            self.state_card,
            self.model_card,
            self.activity_card,
            self.chat_card,
            self.runtime_card,
        ):
            layout.addWidget(card)

        # Arcade Card (collapsed / hidden by default when closed; no idle snake preview)
        self.arcade_card = AtlasArcadeCard(self)
        layout.addWidget(self.arcade_card)

        # Backward compatibility attribute for tests inspecting statusbar.snake_card
        self.snake_card = self.arcade_card.snake_card

        layout.addStretch(1)

        # Thinking-specific contextual Arcade invitation (shown only while AI is thinking)
        self.thinking_arcade_prompt = QFrame()
        self.thinking_arcade_prompt.setObjectName("ThinkingArcadePrompt")
        self.thinking_arcade_prompt.setStyleSheet(
            """
            QFrame#ThinkingArcadePrompt {
                background-color: #18181C;
                border: 1px solid #27272F;
                border-left: 2px solid #4FB8BA;
                border-radius: 4px;
                padding: 4px;
                margin-bottom: 8px;
            }
            """
        )
        prompt_layout = QHBoxLayout(self.thinking_arcade_prompt)
        prompt_layout.setContentsMargins(6, 4, 6, 4)
        prompt_layout.setSpacing(6)

        lbl = QLabel("AI Thinking... Pass time?")
        lbl.setStyleSheet("color: #A1A1AA; font-size: 8pt;")
        prompt_layout.addWidget(lbl, 1)

        prompt_btn = QPushButton("🎮 Arcade")
        prompt_btn.setCursor(Qt.PointingHandCursor)
        prompt_btn.setFixedHeight(20)
        prompt_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #1F2937;
                color: #4FB8BA;
                border: 1px solid #398C8F;
                border-radius: 3px;
                padding: 1px 6px;
                font-size: 7.5pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #398C8F;
                color: #FFFFFF;
            }
            """
        )
        prompt_btn.clicked.connect(self.open_arcade)
        prompt_layout.addWidget(prompt_btn)

        self.thinking_arcade_prompt.hide()
        layout.addWidget(self.thinking_arcade_prompt)

        # Bottom compact controls: [🧰 Tools] [🎮 Arcade]
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(8)

        self.tools_button = QPushButton("🧰  Tools")
        self.tools_button.setObjectName("StatusToolsButton")
        self.tools_button.setCursor(Qt.PointingHandCursor)
        self.tools_button.setFixedHeight(34)
        self.tools_button.clicked.connect(self.tools_requested.emit)
        button_row.addWidget(self.tools_button, 1)

        self.arcade_button = QPushButton("🎮  Arcade")
        self.arcade_button.setObjectName("StatusArcadeButton")
        self.arcade_button.setCursor(Qt.PointingHandCursor)
        self.arcade_button.setFixedHeight(34)
        self.arcade_button.clicked.connect(self.toggle_arcade)
        button_row.addWidget(self.arcade_button, 1)

        layout.addLayout(button_row)

        # Preserved for backward compatibility with tests checking statusbar.settings_button
        self.settings_button = QPushButton("⚙  Settings")
        self.settings_button.setObjectName("StatusSettingsButton")
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.hide()

        layout.addSpacing(10)

        footer = QLabel("Local • Event-driven • Modular")
        footer.setObjectName("StatusFooter")
        footer.setWordWrap(True)
        layout.addWidget(footer)

    def open_arcade(self):
        self.arcade_card.open_arcade()

    def toggle_arcade(self):
        if self.arcade_card.isVisible():
            self.arcade_card.close_arcade()
        else:
            self.arcade_card.open_arcade()

    def open_settings(self):
        try:
            from gui.widgets.settings_dialog import SettingsDialog
            dialog = SettingsDialog(controller=self.controller, parent=self.window())
            dialog.exec()
        except Exception:
            pass

    def _card(self, heading: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("StatusCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(4)

        title = QLabel(heading)
        title.setObjectName("StatusCardTitle")
        layout.addWidget(title)

        label = QLabel(value)
        label.setObjectName("StatusCardValue")
        label.setWordWrap(True)
        layout.addWidget(label)

        card.value_label = label
        return card

    def _set_state(self, text: str, kind: str):
        self._current_state = kind
        self._current_label = text
        color = self.STATE_COLORS.get(kind, "#82828C")
        label = self.state_card.value_label
        label.setTextFormat(Qt.RichText)
        label.setText(
            f'<span style="color:{color}; font-size:10pt;">●</span>&nbsp; '
            f'<span style="color:#F4F4F5; font-weight:500;">{text}</span>'
        )

    def refresh(self):
        generating = (
            bool(getattr(self.state, "is_generating", False))
            if self.state is not None
            else False
        )

        if generating:
            if self._current_state not in (
                "thinking",
                "responding",
                "tool",
                "searching",
                "generating",
            ):
                self._set_state("Generating", "generating")
        else:
            if self._current_state not in ("error", "offline", "tool"):
                self._set_state("Ready", "ready")

        try:
            from config import MODEL_NAME
            self.model_card.value_label.setText(str(MODEL_NAME))
        except Exception:
            self.model_card.value_label.setText("Local model")

        if generating:
            if self._current_state in ("tool", "searching"):
                self.activity_card.value_label.setText(self._current_label)
            else:
                self.activity_card.value_label.setText("Generating response")
        else:
            self.activity_card.value_label.setText("Idle")

        try:
            conversation = self.controller.get_active_conversation()
            title = getattr(conversation, "title", None)
            msgs = getattr(conversation, "messages", []) or []
            count = len(msgs)
            msg_str = f" · {count} msg{'s' if count != 1 else ''}" if count > 0 else ""
            self.chat_card.value_label.setText(f"{str(title or 'Active chat')}{msg_str}")
        except Exception:
            self.chat_card.value_label.setText("No active chat")

        elapsed = int(time.time() - self._start_time)
        minutes, seconds = divmod(elapsed, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            uptime_str = f"{hours}h {minutes}m"
        elif minutes > 0:
            uptime_str = f"{minutes}m {seconds}s"
        else:
            uptime_str = f"{seconds}s"
        self.runtime_card.value_label.setText(f"Online · {uptime_str}")

    def thinking_started(self, event):
        self._set_state("Thinking", "thinking")
        if self.arcade_card.state == STATE_ARCADE_CLOSED:
            self.thinking_arcade_prompt.show()

    def chunk_received(self, event):
        self._set_state("Responding", "responding")

    def tool_requested(self, event):
        tool_name = str(getattr(event, "tool", "") or "tool").lower()
        if "search" in tool_name:
            self._set_state("Searching", "searching")
        else:
            name = tool_name.replace("_", " ").title()
            self._set_state(f"Using {name}", "tool")

    def tool_finished(self, event):
        if getattr(self.state, "is_generating", False):
            self._set_state("Generating", "generating")
        else:
            self._set_state("Ready", "ready")

    def thinking_finished(self, event):
        self._set_state("Ready", "ready")
        self.thinking_arcade_prompt.hide()

    def error_state(self, event):
        self._set_state("Error", "error")
        self.thinking_arcade_prompt.hide()

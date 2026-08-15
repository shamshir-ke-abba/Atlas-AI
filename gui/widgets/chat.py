"""Atlas V3 chat surface with streaming, cancellable generation and natural bubbles."""

import random

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from core.events import (
    ChunkReceived,
    ErrorOccurred,
    MessageReceived,
    ProfileSetupCompleted,
    ProfileSetupRequested,
    ThinkingFinished,
    ThinkingStarted,
)
from gui.widgets.inputbar import AtlasInputBar
from gui.widgets.message import AtlasMessage
from gui.widgets.profile_setup import ProfileSetupCard


WELCOME_MESSAGES = (
    "Hi there — I’m Atlas. Ready when you are.",
    "Hey! Atlas is online. What are we working on?",
    "Hello! I’m ready to help. Ask me anything.",
    "Atlas online. Let’s get started.",
    "Hi! Give me a task and I’ll take it from there.",
)


class AtlasChat(QWidget):
    def __init__(self, bus, controller=None, parent=None):
        super().__init__(parent)
        self.bus = bus
        self.controller = controller
        self.current_ai_message = None
        self.current_ai_response = ""
        self.is_generating = False
        self.auto_follow = True
        self._programmatic_scroll = False

        self.thinking_frame = 0
        self.thinking_timer = QTimer(self)
        self.thinking_timer.setInterval(360)
        self.thinking_timer.timeout.connect(self.animate_thinking)

        self.bus.subscribe(ChunkReceived, self.handle_response)
        self.bus.subscribe(ThinkingStarted, self.handle_thinking_started)
        self.bus.subscribe(ThinkingFinished, self.handle_thinking_finished)
        self.bus.subscribe(ErrorOccurred, self.handle_error)
        self.bus.subscribe(ProfileSetupRequested, self.show_profile_setup)
        self.bus.subscribe(ProfileSetupCompleted, self.profile_completed)

        self.setObjectName("Chat")
        self.build_ui()
        self.show_welcome()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("ChatHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(22, 8, 22, 7)
        header_layout.setSpacing(0)

        title = QLabel("Atlas")
        title.setObjectName("ChatTitle")
        header_layout.addWidget(title)

        subtitle = QLabel("Local AI Assistant")
        subtitle.setObjectName("ChatSubtitle")
        subtitle.setMaximumHeight(16)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)

        self.messages = QWidget()
        self.messages.setObjectName("MessagesContainer")
        self.messages_layout = QVBoxLayout(self.messages)
        self.messages_layout.setContentsMargins(18, 18, 18, 28)
        self.messages_layout.setSpacing(4)
        self.messages_layout.addStretch(1)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("ChatScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.messages)
        self.scroll.verticalScrollBar().valueChanged.connect(self._scroll_changed)
        layout.addWidget(self.scroll, 1)

        self.input_bar = AtlasInputBar()
        self.input_bar.message_sent.connect(self.handle_message)
        self.input_bar.stop_requested.connect(self.handle_stop_requested)
        layout.addWidget(self.input_bar)

    def add_message(self, sender, text):
        message = AtlasMessage(sender, text)
        self.messages_layout.insertWidget(
            self.messages_layout.count() - 1,
            message,
        )
        QTimer.singleShot(0, self._message_geometry_changed)
        return message

    def _message_geometry_changed(self):
        if self.auto_follow:
            self.scroll_to_bottom(force=True)

    def show_welcome(self):
        self.add_message("Atlas", random.choice(WELCOME_MESSAGES))

    def clear_messages(self):
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.current_ai_message = None
        self.current_ai_response = ""
        self.is_generating = False
        self.stop_thinking()
        self.input_bar.set_generating(False)
        self.auto_follow = True

    def _conversation_messages(self, conversation):
        if conversation is None:
            return []
        if isinstance(conversation, dict):
            messages = conversation.get("messages", [])
            return list(messages) if isinstance(messages, list) else []

        for attr in ("get_messages", "history", "last"):
            fn = getattr(conversation, attr, None)
            if callable(fn):
                try:
                    result = fn()
                    if isinstance(result, list):
                        return list(result)
                except Exception:
                    pass

        for attr in ("messages", "current_messages"):
            result = getattr(conversation, attr, None)
            if isinstance(result, list):
                return list(result)
        return []

    def load_conversation(self, conversation):
        self.clear_messages()
        messages = self._conversation_messages(conversation)

        for message in messages:
            if not isinstance(message, dict):
                continue
            text = str(message.get("text") or message.get("content") or "").strip()
            if not text:
                continue
            role = str(message.get("role", "")).lower()
            sender = str(message.get("sender", "")).lower()
            is_user = message.get("is_user")
            display_sender = (
                "User"
                if is_user is True or role == "user" or sender in ("user", "you")
                else "Atlas"
            )
            self.add_message(display_sender, text)

        if not messages:
            self.show_welcome()
        self.auto_follow = True
        QTimer.singleShot(0, lambda: self.scroll_to_bottom(force=True))

    def handle_message(self, text):
        text = str(text).strip()
        if not text or self.is_generating:
            return

        self.auto_follow = True
        self.current_ai_message = None
        self.current_ai_response = ""
        self.add_message("User", text)
        self.scroll_to_bottom(force=True)
        self.bus.publish(MessageReceived(text))

    def handle_stop_requested(self):
        if not self.is_generating:
            return
        if self.controller is not None:
            try:
                self.controller.stop_generation()
            except Exception:
                pass

    def handle_thinking_started(self, event):
        self.is_generating = True
        self.current_ai_response = ""
        self.auto_follow = True

        if self.current_ai_message is None:
            self.current_ai_message = self.add_message("Atlas", "")

        self.start_thinking()
        self.input_bar.set_generating(True)
        self.scroll_to_bottom(force=True)

    def handle_response(self, event):
        if self.current_ai_message is None:
            self.current_ai_message = self.add_message("Atlas", "")

        self.current_ai_response += str(event.text)
        self.stop_thinking()
        self.current_ai_message.set_text(self.current_ai_response)

        # Only follow the stream if the user was already at the bottom.
        if self.auto_follow:
            QTimer.singleShot(0, lambda: self.scroll_to_bottom(force=True))

    def handle_thinking_finished(self, event):
        self.stop_thinking()
        self.is_generating = False
        self.input_bar.set_generating(False)

        if self.current_ai_message is not None:
            self.current_ai_message.set_text(self.current_ai_response)

        if self.auto_follow:
            QTimer.singleShot(0, lambda: self.scroll_to_bottom(force=True))
        self.input_bar.input_field.setFocus()

    def handle_error(self, event):
        self.stop_thinking()
        self.is_generating = False
        self.input_bar.set_generating(False)
        if self.current_ai_message is None:
            self.current_ai_message = self.add_message("Atlas", "")
        self.current_ai_response = str(event.message)
        self.current_ai_message.set_text(self.current_ai_response)
        if self.auto_follow:
            QTimer.singleShot(0, lambda: self.scroll_to_bottom(force=True))

    def start_thinking(self):
        if not self.thinking_timer.isActive():
            self.thinking_frame = 0
            self.thinking_timer.start()

    def stop_thinking(self):
        if self.thinking_timer.isActive():
            self.thinking_timer.stop()

    def animate_thinking(self):
        if self.current_ai_message is None:
            return
        frames = ("•", "••", "•••", "••")
        frame = frames[self.thinking_frame % len(frames)]
        self.thinking_frame += 1
        self.current_ai_message.set_thinking(frame)
        if self.auto_follow:
            self.scroll_to_bottom(force=True)

    def show_profile_setup(self, event):
        if event.prompt:
            self.add_message("Atlas", event.prompt)
        card = ProfileSetupCard(event.tool, controller=self.controller)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, card)
        QTimer.singleShot(0, self._message_geometry_changed)

    def profile_completed(self, event):
        self.add_message(
            "Atlas",
            event.message or "Profile saved. I’ll use it to tailor future suggestions.",
        )
        QTimer.singleShot(0, self._message_geometry_changed)

    def _scroll_changed(self, value):
        if self._programmatic_scroll:
            return
        bar = self.scroll.verticalScrollBar()
        distance = bar.maximum() - value
        if distance <= 24:
            self.auto_follow = True
        elif self.is_generating:
            self.auto_follow = False

    def scroll_to_bottom(self, force=False):
        if not force and not self.auto_follow:
            return
        bar = self.scroll.verticalScrollBar()
        self._programmatic_scroll = True
        try:
            bar.setValue(bar.maximum())
        finally:
            self._programmatic_scroll = False

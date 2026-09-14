"""
Atlas V3 Native Settings Dialog.

Provides native controls for:
- Memory context management (inspect and clear memory)
- Conversation history management (clear all conversations with confirmation)
- Accessibility preferences (reduced motion toggle)
- Theme preference
"""

from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from gui.theme import is_reduced_motion, set_reduced_motion


class SettingsDialog(QDialog):
    """Native settings dialog conforming to the locked Atlas design system."""

    def __init__(self, controller=None, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("SettingsDialog")
        self.setWindowTitle("Atlas Settings")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.resize(560, 600)
        self.build_ui()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Title
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title = QLabel("Settings")
        title.setObjectName("SettingsTitle")
        title.setStyleSheet("font-size: 16pt; font-weight: 600; color: #F4F4F5;")
        header_layout.addWidget(title)

        subtitle = QLabel("Manage Atlas memory, history, and preferences.")
        subtitle.setObjectName("SettingsSubtitle")
        subtitle.setStyleSheet("font-size: 10.5pt; color: #A1A1AA;")
        header_layout.addWidget(subtitle)
        root.addLayout(header_layout)

        scroll = QScrollArea()
        scroll.setObjectName("ToolScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 8, 0, 8)
        content_layout.setSpacing(18)

        # Section 1: Memory Context
        memory_card = QFrame()
        memory_card.setObjectName("SettingsSection")
        memory_card.setStyleSheet(
            "background-color: #121215; border: 1px solid #27272F; border-radius: 8px; padding: 14px;"
        )
        mem_layout = QVBoxLayout(memory_card)
        mem_layout.setSpacing(8)

        mem_title = QLabel("MEMORY CONTEXT")
        mem_title.setStyleSheet("font-size: 9.5pt; font-weight: 600; color: #82828C; letter-spacing: 0.5px;")
        mem_layout.addWidget(mem_title)

        mem_desc = QLabel("Atlas remembers persistent facts and preferences across sessions.")
        mem_desc.setWordWrap(True)
        mem_desc.setStyleSheet("font-size: 10pt; color: #A1A1AA;")
        mem_layout.addWidget(mem_desc)

        self.memory_browser = QTextBrowser()
        self.memory_browser.setObjectName("SettingsMemoryBrowser")
        self.memory_browser.setMaximumHeight(140)
        self.memory_browser.setStyleSheet(
            "background-color: #09090B; border: 1px solid #27272F; border-radius: 6px; "
            "color: #F4F4F5; font-family: 'JetBrains Mono', Consolas, monospace; font-size: 9.5pt; padding: 6px;"
        )
        mem_layout.addWidget(self.memory_browser)

        mem_buttons = QHBoxLayout()
        mem_buttons.addStretch(1)
        self.clear_memory_btn = QPushButton("Clear Memory")
        self.clear_memory_btn.setObjectName("SettingsDangerButton")
        self.clear_memory_btn.setStyleSheet(
            "background-color: #1C1C22; color: #F87171; border: 1px solid #27272F; "
            "border-radius: 6px; padding: 6px 14px; font-size: 10pt; font-weight: 500;"
        )
        self.clear_memory_btn.clicked.connect(self.clear_memory)
        mem_buttons.addWidget(self.clear_memory_btn)
        mem_layout.addLayout(mem_buttons)

        content_layout.addWidget(memory_card)

        # Section 2: Chat History
        history_card = QFrame()
        history_card.setObjectName("SettingsSection")
        history_card.setStyleSheet(
            "background-color: #121215; border: 1px solid #27272F; border-radius: 8px; padding: 14px;"
        )
        hist_layout = QVBoxLayout(history_card)
        hist_layout.setSpacing(8)

        hist_title = QLabel("CHAT HISTORY")
        hist_title.setStyleSheet("font-size: 9.5pt; font-weight: 600; color: #82828C; letter-spacing: 0.5px;")
        hist_layout.addWidget(hist_title)

        hist_desc = QLabel("Manage your conversation store. Clearing history will remove all local chat sessions.")
        hist_desc.setWordWrap(True)
        hist_desc.setStyleSheet("font-size: 10pt; color: #A1A1AA;")
        hist_layout.addWidget(hist_desc)

        hist_buttons = QHBoxLayout()
        hist_buttons.addStretch(1)
        self.clear_history_btn = QPushButton("Clear All Conversations")
        self.clear_history_btn.setObjectName("SettingsDangerButton")
        self.clear_history_btn.setStyleSheet(
            "background-color: #1C1C22; color: #F87171; border: 1px solid #27272F; "
            "border-radius: 6px; padding: 6px 14px; font-size: 10pt; font-weight: 500;"
        )
        self.clear_history_btn.clicked.connect(self.clear_history)
        hist_buttons.addWidget(self.clear_history_btn)
        hist_layout.addLayout(hist_buttons)

        content_layout.addWidget(history_card)

        # Section 3: Preferences
        pref_card = QFrame()
        pref_card.setObjectName("SettingsSection")
        pref_card.setStyleSheet(
            "background-color: #121215; border: 1px solid #27272F; border-radius: 8px; padding: 14px;"
        )
        pref_layout = QVBoxLayout(pref_card)
        pref_layout.setSpacing(10)

        pref_title = QLabel("PREFERENCES & ACCESSIBILITY")
        pref_title.setStyleSheet("font-size: 9.5pt; font-weight: 600; color: #82828C; letter-spacing: 0.5px;")
        pref_layout.addWidget(pref_title)

        self.motion_check = QCheckBox("Reduced motion (disable trajectory animations and pulsing)")
        self.motion_check.setChecked(is_reduced_motion())
        self.motion_check.setStyleSheet("color: #F4F4F5; font-size: 10pt;")
        self.motion_check.toggled.connect(self.toggle_reduced_motion)
        pref_layout.addWidget(self.motion_check)

        theme_row = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet("color: #A1A1AA; font-size: 10pt;")
        theme_val = QLabel("Dark (Locked Canonical)")
        theme_val.setStyleSheet("color: #F4F4F5; font-weight: 500; font-size: 10pt;")
        theme_row.addWidget(theme_label)
        theme_row.addWidget(theme_val)
        theme_row.addStretch(1)
        pref_layout.addLayout(theme_row)

        content_layout.addWidget(pref_card)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # Dialog Footer
        footer = QHBoxLayout()
        footer.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.setObjectName("SettingsCloseButton")
        close_btn.setStyleSheet(
            "background-color: #1C1C22; color: #F4F4F5; border: 1px solid #27272F; "
            "border-radius: 6px; padding: 8px 20px; font-size: 10pt; font-weight: 500;"
        )
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)
        root.addLayout(footer)

        self.refresh_memory_display()

    def refresh_memory_display(self):
        try:
            from core.memory import MemoryManager
            mem = MemoryManager()
            data = mem.all()
            # Clean up empty categories for display
            populated = {k: v for k, v in data.items() if v}
            if populated:
                formatted = json.dumps(populated, indent=2)
                self.memory_browser.setPlainText(formatted)
            else:
                self.memory_browser.setPlainText("No memories stored yet.")
        except Exception as exc:
            self.memory_browser.setPlainText(f"Could not load memory: {exc}")

    def clear_memory(self):
        reply = QMessageBox.question(
            self,
            "Clear Memory",
            "Are you sure you want to clear all stored user memory facts?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                from core.memory import MemoryManager
                mem = MemoryManager()
                mem.clear()
                self.refresh_memory_display()
                QMessageBox.information(self, "Memory Cleared", "All persistent memory facts have been cleared.")
            except Exception as exc:
                QMessageBox.warning(self, "Error", f"Failed to clear memory: {exc}")

    def clear_history(self):
        reply = QMessageBox.question(
            self,
            "Clear Chat History",
            "Are you sure you want to delete ALL conversation history?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                if self.controller is not None:
                    # Delete all conversations from store
                    conversations = self.controller.get_conversations()
                    for conv in list(conversations):
                        cid = conv.get("id") if isinstance(conv, dict) else getattr(conv, "id", None)
                        if cid:
                            try:
                                self.controller.delete_conversation(cid)
                            except Exception:
                                pass
                    self.controller.create_conversation()

                    # Trigger UI update
                    win = self.parent()
                    if win is not None and hasattr(win, "sidebar"):
                        win.sidebar.refresh_history()
                    if win is not None and hasattr(win, "chat"):
                        win.chat.clear_messages()
                        win.chat.show_welcome()

                QMessageBox.information(self, "History Cleared", "All conversations have been deleted.")
            except Exception as exc:
                QMessageBox.warning(self, "Error", f"Failed to clear history: {exc}")

    def toggle_reduced_motion(self, checked: bool):
        set_reduced_motion(checked)

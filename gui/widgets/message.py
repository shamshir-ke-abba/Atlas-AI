"""Atlas V3 chat message bubbles.

The conversation viewport is the only scrollable surface. Individual message
bubbles grow naturally with their text and never contain a scrollbar.
"""

from __future__ import annotations

import html
from pathlib import Path
import re

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


from gui.widgets.state_indicator import AtlasStateIndicator


def markdown_to_html(text: str) -> str:
    """Convert supported Markdown formatting to HTML for RichText display."""
    # Repeatedly unescape HTML entities to collapse double-encoding (e.g. "&amp;#x27;" -> "'")
    raw = str(text or "")
    prev = None
    while raw != prev:
        prev = raw
        raw = html.unescape(raw)

    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    raw = re.sub(r"</?(?:p|div)>", "\n", raw, flags=re.IGNORECASE)

    # Escape only the characters that would produce unintended HTML markup
    # but preserve quotes/apostrophes for readable text.
    text = html.escape(raw, quote=False)

    # Code blocks
    text = re.sub(
        r"```(?:[^\n]*)\n(.*?)```",
        lambda m: (
            '<pre style="white-space:pre-wrap; margin:8px 0; padding:10px; '
            'background-color:#09090B; border:1px solid #27272F; border-radius:6px; '
            'font-family:\'JetBrains Mono\', Consolas, monospace; color:#F4F4F5; font-size:10pt;">'
            + m.group(1)
            + "</pre>"
        ),
        text,
        flags=re.DOTALL,
    )

    # Headings
    text = re.sub(r"^### (.+)$", r'<h3 style="color:#F4F4F5; margin:6px 0 4px 0; font-size:12pt;">\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r"^## (.+)$", r'<h2 style="color:#F4F4F5; margin:8px 0 4px 0; font-size:13pt;">\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r"^# (.+)$", r'<h1 style="color:#F4F4F5; margin:10px 0 6px 0; font-size:15pt;">\1</h1>', text, flags=re.MULTILINE)

    # Inline emphasis & code
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(
        r"`([^`]+)`",
        r'<code style="font-family:\'JetBrains Mono\', Consolas, monospace; background-color:#09090B; border:1px solid #27272F; border-radius:3px; padding:1px 4px; color:#4FB8BA; font-size:10pt;">\1</code>',
        text,
    )

    # Links
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2" style="color:#4FB8BA; text-decoration:underline;">\1</a>',
        text,
    )

    return text.replace("\n", "<br>")


class AtlasMessage(QWidget):
    def __init__(self, sender: str, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.sender = str(sender)
        self.text = str(text or "")
        self.is_user = self.sender.strip().lower() in ("user", "you")
        self._last_parent_width = 0
        self.setObjectName("UserMessage" if self.is_user else "AtlasMessage")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.build_ui()

    def build_ui(self):
        self.outer_layout = QHBoxLayout(self)
        self.outer_layout.setContentsMargins(16, 2, 16, 2)
        self.outer_layout.setSpacing(0)

        self.container = QFrame()
        self.container.setObjectName(
            "UserMessageContainer" if self.is_user else "AtlasMessageContainer"
        )
        self.container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(16, 12, 16, 14)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        if not self.is_user:
            self.avatar_label = QLabel()
            self.avatar_label.setObjectName("AtlasMicroMark")
            self.avatar_label.setFixedSize(16, 16)
            avatar_path = (
                Path(__file__).resolve().parents[2] / "assets" / "atlas_micro_mark.svg"
            )
            if not avatar_path.exists():
                avatar_path = (
                    Path(__file__).resolve().parents[2] / "assets" / "atlas_mark.svg"
                )
            if avatar_path.exists():
                pix = QIcon(str(avatar_path)).pixmap(16, 16)
                if not pix.isNull():
                    self.avatar_label.setPixmap(pix)
            header.addWidget(self.avatar_label)

        self.sender_label = QLabel(self.sender)
        self.sender_label.setObjectName(
            "UserSender" if self.is_user else "AtlasSender"
        )
        header.addWidget(self.sender_label)
        header.addStretch(1)

        if not self.is_user:
            self.copy_button = QToolButton()
            self.copy_button.setObjectName("MessageCopyButton")
            self.copy_button.setText("⧉")
            self.copy_button.setToolTip("Copy response")
            self.copy_button.setCursor(Qt.PointingHandCursor)
            self.copy_button.setAutoRaise(True)
            self.copy_button.setFixedSize(24, 24)
            self.copy_button.clicked.connect(self.copy_message)
            header.addWidget(self.copy_button, 0, Qt.AlignTop)

        layout.addLayout(header)

        self.message_label = QLabel()
        self.message_label.setObjectName(
            "UserMessageText" if self.is_user else "AtlasMessageText"
        )
        self.message_label.setTextFormat(Qt.RichText)
        self.message_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self.message_label.setOpenExternalLinks(True)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.message_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
        layout.addWidget(self.message_label)

        if not self.is_user:
            self.state_indicator = AtlasStateIndicator(self.container)
            layout.addWidget(self.state_indicator)
            self.state_indicator.hide()

        if self.is_user:
            self.outer_layout.addStretch(1)
            self.outer_layout.addWidget(self.container, 0, Qt.AlignRight)
        else:
            self.outer_layout.addWidget(self.container, 0, Qt.AlignLeft)
            self.outer_layout.addStretch(1)

        if self.text:
            self.set_text(self.text)
        elif not self.is_user:
            self.set_state("thinking", "Thinking")
        else:
            self.set_text("")

    def copy_message(self):
        QApplication.clipboard().setText(self.text)
        if hasattr(self, "copy_button"):
            self.copy_button.setText("✓")
            QTimer.singleShot(900, self._restore_copy_icon)

    def _restore_copy_icon(self):
        if hasattr(self, "copy_button"):
            self.copy_button.setText("⧉")

    def set_text(self, text: str):
        self.text = str(text or "")
        if hasattr(self, "state_indicator"):
            self.state_indicator.stop()
            self.state_indicator.hide()
        self.message_label.show()
        self.message_label.setTextFormat(Qt.RichText)
        self.message_label.setText(markdown_to_html(self.text))
        self._resize_bubble()

    def set_state(self, kind: str, label: str = ""):
        if not self.is_user and hasattr(self, "state_indicator"):
            self.message_label.hide()
            self.state_indicator.show()
            self.state_indicator.set_state(kind, label)
            self._resize_bubble()

    def set_thinking(self, frame: str = ""):
        self.set_state("thinking", "Thinking")

    def finish_state(self):
        if hasattr(self, "state_indicator"):
            self.state_indicator.stop()
            if not self.text:
                self.state_indicator.set_state("ready", "Ready")

    def _resize_bubble(self):
        available = self.width()
        if available <= 0 and self.parentWidget():
            available = self.parentWidget().width()
        if available <= 0:
            available = 700

        MAX_COLUMN_WIDTH = 740
        MIN_SIDE_MARGIN = 16

        # Center readable conversation column when space permits
        if available >= MAX_COLUMN_WIDTH + 2 * MIN_SIDE_MARGIN:
            col_width = MAX_COLUMN_WIDTH
            side_margin = (available - col_width) // 2
        else:
            side_margin = MIN_SIDE_MARGIN
            col_width = max(220, available - 2 * side_margin)

        self.outer_layout.setContentsMargins(side_margin, 2, side_margin, 2)

        if self.is_user:
            # User messages: right-aligned, max ~80% of readable column width
            max_user_width = max(180, int(col_width * 0.80))
            max_content_w = max(140, max_user_width - 32)
            fm = self.message_label.fontMetrics()
            rect = fm.boundingRect(
                QRect(0, 0, max_content_w, 10000),
                Qt.TextWordWrap,
                self.text or "...",
            )
            natural_bubble_w = rect.width() + 36
            bubble_width = min(max_user_width, max(140, natural_bubble_w))
        else:
            # Atlas messages: left-aligned, full-width across readable column
            bubble_width = col_width

        self.container.setFixedWidth(bubble_width)
        content_width = max(140, bubble_width - 32)
        self.message_label.setFixedWidth(content_width)
        if hasattr(self, "state_indicator"):
            self.state_indicator.setFixedWidth(content_width)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_width = event.size().width()
        if new_width > 0 and new_width != self._last_parent_width:
            self._last_parent_width = new_width
            self._resize_bubble()


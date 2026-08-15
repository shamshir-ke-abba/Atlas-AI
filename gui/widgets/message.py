"""Atlas V3 chat message bubbles.

The conversation viewport is the only scrollable surface. Individual message
bubbles grow naturally with their text and never contain a scrollbar.
"""

import html
import re

from PySide6.QtCore import Qt, QTimer
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


def markdown_to_html(text):
    # Repeatedly unescape HTML entities to collapse double-encoding (e.g. "&amp;#x27;" -> "'")
    raw = str(text or "")
    prev = None
    while raw != prev:
        prev = raw
        raw = html.unescape(raw)

    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    raw = re.sub(r"</?(?:p|div)>", "\n", raw, flags=re.IGNORECASE)

    # Escape only the characters that would produce unintended HTML markup
    # but preserve quotes/apostrophes for readable text. This prevents
    # single quotes from being converted to numeric entities like &#x27;.
    text = html.escape(raw, quote=False)
    text = re.sub(
        r"```(?:[^\n]*)\n(.*?)```",
        lambda m: (
            '<pre style="white-space:pre-wrap; margin:8px 0; '
            'font-family:monospace;">' + m.group(1) + "</pre>"
        ),
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r"^### (.+)$", r"<h3>\1</h3>", text, flags=re.MULTILINE)
    text = re.sub(r"^## (.+)$", r"<h2>\1</h2>", text, flags=re.MULTILINE)
    text = re.sub(r"^# (.+)$", r"<h1>\1</h1>", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2">\1</a>',
        text,
    )
    return text.replace("\n", "<br>")


class AtlasMessage(QWidget):
    def __init__(self, sender, text, parent=None):
        super().__init__(parent)
        self.sender = str(sender)
        self.text = str(text or "")
        self.is_user = self.sender.strip().lower() in ("user", "you")
        self._last_parent_width = 0
        self.setObjectName("UserMessage" if self.is_user else "AtlasMessage")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.build_ui()

    def build_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 6, 12, 8)
        outer.setSpacing(0)

        self.container = QFrame()
        self.container.setObjectName(
            "UserMessageContainer" if self.is_user else "AtlasMessageContainer"
        )
        self.container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
        self.container.setStyleSheet(
            "QFrame#AtlasMessageContainer {"
            "background:#202020; border:1px solid #303030; border-radius:14px;}"
            "QFrame#UserMessageContainer {"
            "background:#292929; border:1px solid #383838; border-radius:14px;}"
        )

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(7)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

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
            self.copy_button.setFixedSize(28, 28)
            self.copy_button.setStyleSheet(
                "QToolButton#MessageCopyButton { border:0; background:transparent; "
                "color:#9d9d9d; border-radius:6px; font-size:16px; }"
                "QToolButton#MessageCopyButton:hover { background:#303030; color:#fff; }"
            )
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
        self.message_label.setStyleSheet(
            "QLabel { background:transparent; border:0; color:#f2f2f2; "
            "font-size:15px; padding:0; }"
        )
        layout.addWidget(self.message_label)

        if self.is_user:
            outer.addStretch(1)
            outer.addWidget(self.container, 0, Qt.AlignRight)
        else:
            outer.addWidget(self.container, 0, Qt.AlignLeft)
            outer.addStretch(1)

        self.set_text(self.text)

    def copy_message(self):
        QApplication.clipboard().setText(self.text)
        if hasattr(self, "copy_button"):
            self.copy_button.setText("✓")
            QTimer.singleShot(900, self._restore_copy_icon)

    def _restore_copy_icon(self):
        if hasattr(self, "copy_button"):
            self.copy_button.setText("⧉")

    def set_text(self, text):
        self.text = str(text or "")
        # Ensure we render via the single RichText pipeline so
        # partial streamed chunks are interpreted consistently
        # (prevents showing literal HTML tags when the label
        # was previously switched to PlainText by thinking frames).
        self.message_label.setTextFormat(Qt.RichText)
        self.message_label.setText(markdown_to_html(self.text))
        self._resize_bubble()

    def _resize_bubble(self):
        parent = self.parentWidget()
        available = parent.width() if parent is not None else 1000
        available = max(500, available)

        if self.is_user:
            width = min(650, max(220, int(available * 0.60)))
        else:
            width = min(980, max(430, int(available * 0.84)))

        self.container.setFixedWidth(width)
        content_width = max(180, width - 32)
        self.message_label.setFixedWidth(content_width)
        self.message_label.adjustSize()
        self.container.adjustSize()
        self.adjustSize()
        self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        parent_width = self.parentWidget().width() if self.parentWidget() else 0
        if parent_width != self._last_parent_width:
            self._last_parent_width = parent_width
            QTimer.singleShot(0, self._resize_bubble)

    def set_thinking(self, frame):
        self.message_label.setTextFormat(Qt.PlainText)
        self.message_label.setText(str(frame))
        self.message_label.adjustSize()
        self.container.adjustSize()
        self.adjustSize()

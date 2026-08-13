"""
gui/widgets/message.py

Atlas Chat Message Widget.
"""

import re
import html

from PySide6.QtCore import (
    Qt,
    QUrl,
)

from PySide6.QtGui import (
    QDesktopServices,
)

from PySide6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QTextBrowser,
)


class AtlasMessage(QWidget):

    MAX_BUBBLE_WIDTH = 560

    def __init__(
        self,
        sender,
        text,
        parent=None,
    ):

        super().__init__(parent)

        self.sender = sender
        self.text = text

        self.is_user = (
            sender.lower()
            == "user"
        )

        self.setObjectName(
            "MessageUser"
            if self.is_user
            else "MessageAtlas"
        )

        self.build_ui()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        main_layout = QHBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            0,
            4,
            0,
            4,
        )

        main_layout.setSpacing(
            0
        )

        # ---------------------------------
        # Content
        # ---------------------------------

        bubble = QWidget()

        bubble.setObjectName(
            "MessageBubble"
        )

        bubble.setMaximumWidth(
            self.MAX_BUBBLE_WIDTH
        )

        content_layout = QVBoxLayout(
            bubble
        )

        content_layout.setContentsMargins(
            14,
            10,
            14,
            10,
        )

        content_layout.setSpacing(
            4
        )

        # ---------------------------------
        # Sender
        # ---------------------------------

        self.sender_label = QLabel(
            self.sender
        )

        self.sender_label.setObjectName(
            "MessageSender"
        )

        if self.is_user:

            self.sender_label.setAlignment(
                Qt.AlignRight
            )

        content_layout.addWidget(
            self.sender_label
        )

        # ---------------------------------
        # Message
        # ---------------------------------

        self.message_label = QTextBrowser()

        self.message_label.setObjectName(
            "MessageText"
        )

        self.message_label.setReadOnly(
            True
        )

        self.message_label.setFrameShape(
            QTextBrowser.NoFrame
        )

        self.message_label.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.message_label.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.message_label.setOpenLinks(
            False
        )

        self.message_label.setOpenExternalLinks(
            False
        )

        self.message_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
            | Qt.TextSelectableByKeyboard
            | Qt.LinksAccessibleByMouse
            | Qt.LinksAccessibleByKeyboard
        )

        self.message_label.anchorClicked.connect(
            self.open_link
        )

        self.set_message_text(
            self.text
        )

        content_layout.addWidget(
            self.message_label
        )

        # ---------------------------------
        # Alignment
        #
        # Atlas -> left
        # User  -> right
        # ---------------------------------

        if self.is_user:

            main_layout.addStretch(
                1
            )

            main_layout.addWidget(
                bubble,
                0,
                Qt.AlignRight,
            )

        else:

            main_layout.addWidget(
                bubble,
                0,
                Qt.AlignLeft,
            )

            main_layout.addStretch(
                1
            )

    # =====================================================
    # Markdown / Link Rendering
    # =====================================================

    @staticmethod
    def markdown_to_html(
        text,
    ):

        if not text:
            return ""

        # ---------------------------------
        # Escape HTML
        # ---------------------------------

        text = html.escape(
            text
        )

        # ---------------------------------
        # Markdown links
        #
        # [Ubuntu](https://ubuntu.com)
        # ---------------------------------

        text = re.sub(
            r'\[([^\]]+)\]\((https?://[^\s\)]+)\)',
            r'<a href="\2">\1</a>',
            text,
            flags=re.IGNORECASE,
        )

        # ---------------------------------
        # Plain URLs
        # ---------------------------------

        parts = re.split(
            r'(<a\s+href="[^"]+">.*?</a>)',
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        for index in range(
            0,
            len(parts),
            2,
        ):

            parts[index] = re.sub(
                r'(?<!["=])(https?://[^\s<]+)',
                r'<a href="\1">\1</a>',
                parts[index],
                flags=re.IGNORECASE,
            )

        text = "".join(
            parts
        )

        # ---------------------------------
        # Bold
        # ---------------------------------

        text = re.sub(
            r'\*\*(.+?)\*\*',
            r'<strong>\1</strong>',
            text,
            flags=re.DOTALL,
        )

        # ---------------------------------
        # Inline code
        # ---------------------------------

        text = re.sub(
            r'`([^`]+)`',
            r'<code>\1</code>',
            text,
        )

        # ---------------------------------
        # New lines
        # ---------------------------------

        text = text.replace(
            "\n",
            "<br>",
        )

        return text

    # =====================================================
    # Set Message
    # =====================================================

    def set_message_text(
        self,
        text,
    ):

        self.message_label.setHtml(
            self.markdown_to_html(
                text
            )
        )

        self._adjust_height()

    def _adjust_height(self):

        document = (
            self.message_label
            .document()
        )

        document.setTextWidth(
            self.message_label
            .viewport()
            .width()
        )

        height = int(
            document.size()
            .height()
        ) + 8

        self.message_label.setFixedHeight(
            max(
                height,
                24,
            )
        )

    # =====================================================
    # Open Link
    # =====================================================

    def open_link(
        self,
        url,
    ):

        if not isinstance(
            url,
            QUrl,
        ):

            url = QUrl(
                str(url)
            )

        if not url.isValid():
            return

        QDesktopServices.openUrl(
            url
        )

    # =====================================================
    # Public API
    # =====================================================

    def set_text(
        self,
        text,
    ):

        self.text = text

        self.set_message_text(
            text
        )

    # =====================================================
    # Thinking Indicator
    # =====================================================

    def set_thinking(
        self,
        thinking=True,
    ):

        if thinking:

            self.message_label.setPlainText(
                "● ● ●"
            )

            self.message_label.setFixedHeight(
                24
            )

        else:

            self.set_message_text(
                self.text
            )

    def resizeEvent(
        self,
        event,
    ):

        super().resizeEvent(
            event
        )

        self._adjust_height()

"""
AtlasAI V3 — Chat Widget (Complete and Working)
Fixed to properly handle conversation loading and streaming responses
"""

import logging
from typing import List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class ChatMessage(QWidget):
    """Individual chat message widget."""

    def __init__(self, sender: str, text: str, is_user: bool = False, parent=None):
        super().__init__(parent)
        self.sender = sender
        self.text = text
        self.is_user = is_user
        self.text_label = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup message UI with proper styling."""
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # Sender label
        sender_label = QLabel(self.sender)
        sender_font = QFont()
        sender_font.setBold(True)
        sender_font.setPointSize(10)
        sender_label.setFont(sender_font)
        
        if self.is_user:
            sender_label.setStyleSheet("color: #0066cc;")
        else:
            sender_label.setStyleSheet("color: #888;")
        
        layout.addWidget(sender_label)
        
        # Message text - Store reference for updates
        self.text_label = QLabel(self.text)
        self.text_label.setWordWrap(True)
        text_font = QFont()
        text_font.setPointSize(10)
        self.text_label.setFont(text_font)
        self.text_label.setStyleSheet("color: #ffffff;")
        
        layout.addWidget(self.text_label)
        
        # Set background color based on sender
        if self.is_user:
            self.setStyleSheet(
                "QWidget { "
                "  background-color: #0066cc; "
                "  border-radius: 8px; "
                "  padding: 12px; "
                "}"
            )
        else:
            self.setStyleSheet(
                "QWidget { "
                "  background-color: #252525; "
                "  border-radius: 8px; "
                "  padding: 12px; "
                "}"
            )

    def append_text(self, text: str) -> None:
        """Append text to message."""
        self.text += text
        if self.text_label:
            self.text_label.setText(self.text)

    def get_text(self) -> str:
        """Get message text."""
        return self.text


class ChatWidget(QWidget):
    """Main chat area with message display and input."""
    
    # Signals
    message_sent = Signal(str)
    conversation_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.messages: List[Dict[str, Any]] = []
        self.message_widgets: List[ChatMessage] = []
        self.current_atlas_message_widget: ChatMessage = None
        
        self._setup_ui()
        self.setStyleSheet("QWidget { background-color: #1e1e1e; }")

    def _setup_ui(self):
        """Setup the chat widget UI."""
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            "QScrollArea { "
            "  background-color: #1e1e1e; "
            "  border: none; "
            "}"
        )
        
        # Message container
        self.message_container = QWidget()
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(16, 16, 16, 16)
        self.message_layout.setSpacing(12)
        self.message_layout.addStretch()
        
        self.message_container.setStyleSheet(
            "QWidget { background-color: #1e1e1e; }"
        )
        
        self.scroll_area.setWidget(self.message_container)
        layout.addWidget(self.scroll_area)

    # ================================================
    # Message Management
    # ================================================

    def clear_messages(self) -> None:
        """Clear all messages from the chat. CRITICAL FIX."""
        
        logger.info("Clearing chat messages")
        
        # Remove all message widgets except stretch
        while self.message_layout.count() > 1:
            item = self.message_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear tracking lists
        self.messages.clear()
        self.message_widgets.clear()
        self.current_atlas_message_widget = None
        
        self._scroll_to_bottom()
        logger.debug("Chat cleared successfully")

    def add_message(
        self,
        sender: str,
        text: str,
        is_user: bool = False
    ) -> ChatMessage:
        """Add a message to the chat.
        
        Args:
            sender: Name of sender ("You" or "Atlas")
            text: Message text
            is_user: True if user message, False if Atlas
            
        Returns:
            The ChatMessage widget created
        """
        
        logger.debug(f"Adding message from {sender}: {text[:50] if text else '(empty)'}...")
        
        # Create message widget
        msg_widget = ChatMessage(
            sender=sender,
            text=text,
            is_user=is_user,
            parent=self.message_container
        )
        
        # Insert before stretch (count - 1)
        insert_pos = self.message_layout.count() - 1
        self.message_layout.insertWidget(insert_pos, msg_widget)
        
        # Track message
        self.messages.append({
            'sender': sender,
            'text': text,
            'is_user': is_user,
        })
        
        self.message_widgets.append(msg_widget)
        
        # If this is Atlas message, track it for streaming
        if not is_user:
            self.current_atlas_message_widget = msg_widget
        
        self._scroll_to_bottom()
        
        logger.debug(f"Message added. Total messages: {len(self.messages)}")
        
        return msg_widget

    def load_messages(self, messages: List[Dict[str, Any]]) -> None:
        """Load messages from a conversation.
        
        CRITICAL FIX: This properly clears before loading.
        
        Args:
            messages: List of dicts with 'sender', 'text', 'is_user' keys
        """
        
        logger.info(f"Loading {len(messages)} messages into chat")
        
        # CRITICAL FIX: Clear before loading
        self.clear_messages()
        
        if not messages:
            logger.info("No messages to load")
            self.conversation_changed.emit()
            return
        
        # Add each message
        for msg in messages:
            sender = msg.get('sender', 'Unknown')
            text = msg.get('text', '')
            is_user = msg.get('is_user', False)
            
            if text:  # Only add non-empty messages
                self.add_message(sender, text, is_user)
        
        logger.info(f"Successfully loaded and displayed {len(messages)} messages")
        self.conversation_changed.emit()

    def append_to_last_message(self, chunk: str) -> None:
        """Append text to the last Atlas message (for streaming).
        
        Args:
            chunk: Text chunk to append
        """
        
        if not chunk:
            return
        
        logger.debug(f"Appending chunk: {chunk[:30]}...")
        
        # If we have a current Atlas message widget, append to it
        if self.current_atlas_message_widget:
            self.current_atlas_message_widget.append_text(chunk)
            
            # Update tracking
            if self.messages and not self.messages[-1]['is_user']:
                self.messages[-1]['text'] += chunk
        else:
            # No current message, create one
            logger.warning("No current message widget, creating new one")
            self.add_message("Atlas", chunk, is_user=False)
        
        self._scroll_to_bottom()

    def finalize_atlas_message(self) -> None:
        """Finalize the current Atlas message (called after streaming complete)."""
        
        logger.debug("Finalizing Atlas message")
        self.current_atlas_message_widget = None

    def _scroll_to_bottom(self) -> None:
        """Scroll chat to the bottom with delay to ensure layout update."""
        
        # Use QTimer to ensure scroll happens after layout update
        QTimer.singleShot(
            100,
            lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            )
        )

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages currently displayed.
        
        Returns:
            List of message dictionaries
        """
        return self.messages.copy()

    def get_message_count(self) -> int:
        """Get total number of messages."""
        return len(self.messages)

    def get_last_message(self) -> Dict[str, Any]:
        """Get the last message."""
        if self.messages:
            return self.messages[-1]
        return None

    def is_empty(self) -> bool:
        """Check if chat is empty."""
        return len(self.messages) == 0
"""
Sidebar Widget - Conversations and Tools
"""

import logging
from typing import List, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QInputDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class SidebarWidget(QWidget):
    """Sidebar with conversations and tools."""
    
    new_conversation = Signal()
    conversation_selected = Signal(str)  # conversation_id
    tool_selected = Signal(str)  # tool_name
    conversation_renamed = Signal(str, str)  # conversation_id, new_name
    conversation_deleted = Signal(str)  # conversation_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conversations: Dict[str, Dict] = {}
        self.current_conversation_id: str = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup sidebar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("ATLAS")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet("color: #ffffff;")
        layout.addWidget(header)
        
        # New Chat Button
        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #0066cc;"
            "  color: white;"
            "  border: none;"
            "  padding: 10px;"
            "  border-radius: 6px;"
            "  font-weight: bold;"
            "}"
            "QPushButton:hover {"
            "  background-color: #0052a3;"
            "}"
        )
        new_chat_btn.clicked.connect(self._on_new_chat)
        layout.addWidget(new_chat_btn)
        
        # Conversations Section
        chats_label = QLabel("CHATS")
        chats_label_font = QFont()
        chats_label_font.setPointSize(9)
        chats_label_font.setBold(True)
        chats_label.setFont(chats_label_font)
        chats_label.setStyleSheet("color: #888;")
        layout.addWidget(chats_label)
        
        self.conversation_list = QListWidget()
        self.conversation_list.setStyleSheet(
            "QListWidget {"
            "  background-color: transparent;"
            "  border: none;"
            "  outline: none;"
            "}"
            "QListWidget::item {"
            "  padding: 8px;"
            "  border-radius: 4px;"
            "  margin-bottom: 4px;"
            "}"
            "QListWidget::item:selected {"
            "  background-color: #0066cc;"
            "  color: white;"
            "}"
            "QListWidget::item:hover {"
            "  background-color: #333333;"
            "}"
        )
        self.conversation_list.itemClicked.connect(self._on_conversation_clicked)
        self.conversation_list.itemDoubleClicked.connect(self._on_conversation_double_clicked)
        layout.addWidget(self.conversation_list)
        
        # Tools Section
        tools_label = QLabel("TOOLS")
        tools_label_font = QFont()
        tools_label_font.setPointSize(9)
        tools_label_font.setBold(True)
        tools_label.setFont(tools_label_font)
        tools_label.setStyleSheet("color: #888;")
        layout.addWidget(tools_label)
        
        self.tools_list = QListWidget()
        self.tools_list.setStyleSheet(
            "QListWidget {"
            "  background-color: transparent;"
            "  border: none;"
            "  outline: none;"
            "  max-height: 200px;"
            "}"
            "QListWidget::item {"
            "  padding: 8px;"
            "  border-radius: 4px;"
            "  margin-bottom: 4px;"
            "}"
            "QListWidget::item:selected {"
            "  background-color: #0066cc;"
            "  color: white;"
            "}"
            "QListWidget::item:hover {"
            "  background-color: #333333;"
            "}"
        )
        self.tools_list.itemClicked.connect(self._on_tool_clicked)
        layout.addWidget(self.tools_list)
        
        # Settings Button
        layout.addStretch()
        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: transparent;"
            "  color: #888;"
            "  border: 1px solid #444;"
            "  padding: 8px;"
            "  border-radius: 4px;"
            "}"
            "QPushButton:hover {"
            "  color: #ffffff;"
            "  border: 1px solid #666;"
            "}"
        )
        layout.addWidget(settings_btn)
        
        self.setStyleSheet("QWidget { background-color: #121212; }")

    # ================================================
    # Conversation Management
    # ================================================

    def add_conversation(self, conversation_id: str, title: str) -> None:
        """Add conversation to list."""
        logger.info(f"Adding conversation: {conversation_id} - {title}")
        
        self.conversations[conversation_id] = {'title': title}
        
        item = QListWidgetItem(title)
        item.setData(Qt.UserRole, conversation_id)
        self.conversation_list.addItem(item)

    def update_conversations(self, conversations: Dict[str, Dict]) -> None:
        """Update conversation list."""
        logger.info(f"Updating conversations: {len(conversations)} total")
        
        self.conversations = conversations
        self.conversation_list.clear()
        
        for conv_id, metadata in conversations.items():
            title = metadata.get('title', 'Untitled')
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, conv_id)
            self.conversation_list.addItem(item)

    def select_conversation(self, conversation_id: str) -> None:
        """Programmatically select conversation."""
        logger.info(f"Selecting conversation: {conversation_id}")
        
        for i in range(self.conversation_list.count()):
            item = self.conversation_list.item(i)
            if item.data(Qt.UserRole) == conversation_id:
                self.conversation_list.setCurrentItem(item)
                self.current_conversation_id = conversation_id
                break

    def _on_new_chat(self) -> None:
        """Handle new chat button."""
        logger.info("New chat requested")
        self.new_conversation.emit()

    def _on_conversation_clicked(self, item: QListWidgetItem) -> None:
        """Handle conversation selection."""
        conversation_id = item.data(Qt.UserRole)
        logger.info(f"Conversation clicked: {conversation_id}")
        
        self.current_conversation_id = conversation_id
        self.conversation_selected.emit(conversation_id)

    def _on_conversation_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle conversation rename."""
        conversation_id = item.data(Qt.UserRole)
        old_title = item.text()
        
        new_title, ok = QInputDialog.getText(
            self,
            "Rename Conversation",
            "New name:",
            text=old_title
        )
        
        if ok and new_title:
            logger.info(f"Renaming conversation {conversation_id} to {new_title}")
            item.setText(new_title)
            self.conversations[conversation_id]['title'] = new_title
            self.conversation_renamed.emit(conversation_id, new_title)
    
    # ================================================
    # Tools Management
    # ================================================

    def set_available_tools(self, tools: List[Dict]) -> None:
        """Set available tools."""
        logger.info(f"Setting available tools: {len(tools)} tools")
        
        self.tools_list.clear()
        
        for tool in tools:
            name = tool.get('name', 'Unknown')
            icon = tool.get('icon', '🔧')
            
            display_name = f"{icon} {name}"
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, name)
            self.tools_list.addItem(item)

    def _on_tool_clicked(self, item: QListWidgetItem) -> None:
        """Handle tool selection."""
        tool_name = item.data(Qt.UserRole)
        logger.info(f"Tool selected: {tool_name}")
        self.tool_selected.emit(tool_name)
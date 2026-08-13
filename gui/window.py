"""
Main GUI Window - Works with actual brain
"""

import logging
from typing import Optional
from threading import Thread

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QLineEdit, QPushButton, QVBoxLayout
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont

from gui.widgets.chat import ChatWidget
from gui.widgets.sidebar import SidebarWidget
from config import GUI_WINDOW_WIDTH, GUI_WINDOW_HEIGHT

logger = logging.getLogger(__name__)


class MessageWorker(QObject):
    """Worker thread for message processing."""
    
    response_chunk = Signal(str)
    response_complete = Signal()
    response_error = Signal(str)
    
    def __init__(self, controller, conversation_id, message):
        super().__init__()
        self.controller = controller
        self.conversation_id = conversation_id
        self.message = message

    def run(self):
        """Process message in background thread."""
        try:
            for chunk in self.controller.send_message_stream(
                self.conversation_id,
                self.message
            ):
                self.response_chunk.emit(chunk)
            
            self.response_complete.emit()
        
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            self.response_error.emit(str(e))


class AtlasWindow(QMainWindow):
    """Main Atlas GUI window."""
    
    def __init__(self, runtime, parent=None):
        super().__init__(parent)
        
        self.runtime = runtime
        self.current_conversation_id: Optional[str] = None
        self.message_thread: Optional[Thread] = None
        self.is_processing = False
        
        self.setWindowTitle("AtlasAI V3")
        self.setGeometry(100, 100, GUI_WINDOW_WIDTH, GUI_WINDOW_HEIGHT)
        
        self._setup_ui()
        self._connect_signals()
        self._initialize_conversations()
        
        self.setStyleSheet("QMainWindow { background-color: #121212; }")

    def _setup_ui(self):
        """Setup main window UI."""
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = SidebarWidget()
        main_layout.addWidget(self.sidebar, 0)
        
        # Chat area
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Chat display
        self.chat_widget = ChatWidget()
        chat_layout.addWidget(self.chat_widget, 1)
        
        # Input area
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(8)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask Atlas something...")
        self.input_field.setStyleSheet(
            "QLineEdit {"
            "  background-color: #252525;"
            "  color: #ffffff;"
            "  border: 1px solid #444;"
            "  padding: 10px;"
            "  border-radius: 6px;"
            "  font-size: 14px;"
            "}"
            "QLineEdit:focus {"
            "  border: 1px solid #0066cc;"
            "}"
        )
        self.input_field.returnPressed.connect(self._on_send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #0066cc;"
            "  color: white;"
            "  border: none;"
            "  padding: 10px 20px;"
            "  border-radius: 6px;"
            "  font-weight: bold;"
            "}"
            "QPushButton:hover {"
            "  background-color: #0052a3;"
            "}"
        )
        self.send_btn.clicked.connect(self._on_send_message)
        input_layout.addWidget(self.send_btn)
        
        input_container.setStyleSheet("QWidget { background-color: #1e1e1e; }")
        chat_layout.addWidget(input_container)
        
        main_layout.addWidget(chat_container, 1)

    def _connect_signals(self):
        """Connect signals."""
        self.sidebar.new_conversation.connect(self._on_new_conversation)
        self.sidebar.conversation_selected.connect(self._on_conversation_selected)
        self.sidebar.conversation_renamed.connect(self._on_conversation_renamed)
        self.sidebar.conversation_deleted.connect(self._on_conversation_deleted)

    # ================================================
    # Initialization & Loading
    # ================================================

    def _initialize_conversations(self):
        """Load conversations from backend."""
        logger.info("Initializing conversations")
        
        try:
            conversations = self.runtime.controller.get_conversations()
            logger.info(f"Loaded {len(conversations)} conversations")
            
            self.sidebar.update_conversations(conversations)
            
            if conversations:
                first_id = list(conversations.keys())[0]
                self.sidebar.select_conversation(first_id)
                self._load_conversation(first_id)
            else:
                self._on_new_conversation()
        
        except Exception as e:
            logger.error(f"Error initializing conversations: {e}")

    # ================================================
    # Conversation Management
    # ================================================

    def _on_new_conversation(self):
        """Handle new conversation."""
        logger.info("Creating new conversation")
        
        try:
            conversation_id = self.runtime.controller.create_conversation()
            logger.info(f"Created conversation: {conversation_id}")
            
            self.chat_widget.clear_messages()
            self.current_conversation_id = conversation_id
            
            self.sidebar.add_conversation(conversation_id, "New Chat")
            self.sidebar.select_conversation(conversation_id)
        
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")

    def _on_conversation_selected(self, conversation_id: str):
        """Handle conversation selection."""
        logger.info(f"Conversation selected: {conversation_id}")
        
        self.current_conversation_id = conversation_id
        self._load_conversation(conversation_id)

    def _load_conversation(self, conversation_id: str):
        """Load conversation and display messages."""
        logger.info(f"Loading conversation: {conversation_id}")
        
        try:
            conv_data = self.runtime.controller.get_conversation(conversation_id)
            
            if not conv_data:
                logger.warning(f"Conversation not found: {conversation_id}")
                self.chat_widget.clear_messages()
                return
            
            messages = conv_data.get('messages', [])
            logger.info(f"Loaded {len(messages)} messages")
            
            self.chat_widget.load_messages(messages)
            logger.info(f"Successfully displayed {len(messages)} messages")
        
        except Exception as e:
            logger.error(f"Error loading conversation: {e}")
            self.chat_widget.clear_messages()

    def _on_conversation_renamed(self, conversation_id: str, new_title: str):
        """Handle rename."""
        logger.info(f"Renaming conversation {conversation_id} to {new_title}")
        
        try:
            self.runtime.controller.rename_conversation(conversation_id, new_title)
        except Exception as e:
            logger.error(f"Error renaming: {e}")

    def _on_conversation_deleted(self, conversation_id: str):
        """Handle delete."""
        logger.info(f"Deleting conversation: {conversation_id}")
        
        try:
            self.runtime.controller.delete_conversation(conversation_id)
            
            conversations = self.runtime.controller.get_conversations()
            
            if conversations:
                first_id = list(conversations.keys())[0]
                self.sidebar.select_conversation(first_id)
                self._load_conversation(first_id)
            else:
                self._on_new_conversation()
        
        except Exception as e:
            logger.error(f"Error deleting: {e}")

    # ================================================
    # Message Handling
    # ================================================

    def _on_send_message(self):
        """Handle message send."""
        
        if self.is_processing:
            logger.warning("Already processing a message")
            return
        
        text = self.input_field.text().strip()
        
        if not text:
            return
        
        logger.info(f"Sending message: {text[:50]}...")
        
        # Add user message immediately
        self.chat_widget.add_message(sender="You", text=text, is_user=True)
        self.input_field.clear()
        self.send_btn.setEnabled(False)
        self.input_field.setEnabled(False)
        self.is_processing = True
        
        # Create worker
        worker = MessageWorker(
            self.runtime.controller,
            self.current_conversation_id,
            text
        )
        
        # Connect signals
        worker.response_chunk.connect(self._on_response_chunk)
        worker.response_complete.connect(self._on_response_complete)
        worker.response_error.connect(self._on_response_error)
        
        # Run in thread
        self.message_thread = Thread(target=worker.run, daemon=True)
        self.message_thread.start()

    def _on_response_chunk(self, chunk: str):
        """Handle response chunk."""
        self.chat_widget.append_to_last_message(chunk)

    def _on_response_complete(self):
        """Handle response complete."""
        logger.info("Response complete")
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)
        self.is_processing = False

    def _on_response_error(self, error: str):
        """Handle response error."""
        logger.error(f"Response error: {error}")
        self.chat_widget.add_message(sender="Atlas", text=f"Error: {error}", is_user=False)
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)
        self.is_processing = False
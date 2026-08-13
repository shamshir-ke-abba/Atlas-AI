"""
Conversation Management (FIXED)
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from config import CONVERSATIONS_DIR

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages a single conversation."""
    
    def __init__(self, conversation_id: str, title: str = "New Chat"):
        self.id = conversation_id
        self.title = title
        self.created = datetime.now().isoformat()
        self.modified = datetime.now().isoformat()
        self.messages: List[Dict[str, Any]] = []

    def add_message(self, sender: str, text: str, is_user: bool = False) -> None:
        """Add message to conversation."""
        message = {
            'sender': sender,
            'text': text,
            'is_user': is_user,
            'timestamp': datetime.now().isoformat(),
        }
        self.messages.append(message)
        self.modified = datetime.now().isoformat()

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages."""
        return self.messages.copy()

    def clear_messages(self) -> None:
        """Clear all messages."""
        self.messages = []
        self.modified = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'created': self.created,
            'modified': self.modified,
            'messages': self.messages,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ConversationManager':
        """Create from dictionary."""
        conv = ConversationManager(
            data.get('id', ''),
            data.get('title', 'New Chat')
        )
        conv.created = data.get('created', datetime.now().isoformat())
        conv.modified = data.get('modified', datetime.now().isoformat())
        conv.messages = data.get('messages', [])
        return conv


class ConversationStore:
    """Manages all conversations on disk."""
    
    def __init__(self):
        self.conversations_dir = CONVERSATIONS_DIR
        self.conversations_dir.mkdir(parents=True, exist_ok=True)

    def _get_conversation_file(self, conversation_id: str) -> Path:
        """Get file path for conversation."""
        return self.conversations_dir / f"{conversation_id}.json"

    def save(self, manager: ConversationManager) -> bool:
        """Save conversation to disk."""
        try:
            file_path = self._get_conversation_file(manager.id)
            with file_path.open('w', encoding='utf-8') as f:
                json.dump(manager.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved conversation: {manager.id}")
            return True
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return False

    def load(self, conversation_id: str) -> Optional[ConversationManager]:
        """Load conversation from disk."""
        try:
            file_path = self._get_conversation_file(conversation_id)
            if not file_path.exists():
                logger.warning(f"Conversation file not found: {file_path}")
                return None
            
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            
            manager = ConversationManager.from_dict(data)
            logger.info(f"Loaded conversation: {conversation_id}")
            return manager
        except Exception as e:
            logger.error(f"Error loading conversation: {e}")
            return None

    def delete(self, conversation_id: str) -> bool:
        """Delete conversation."""
        try:
            file_path = self._get_conversation_file(conversation_id)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted conversation: {conversation_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False

    def list_all(self) -> Dict[str, Dict]:
        """List all conversations with metadata."""
        conversations = {}
        try:
            for file_path in self.conversations_dir.glob('*.json'):
                try:
                    conversation_id = file_path.stem
                    with file_path.open('r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    conversations[conversation_id] = {
                        'title': data.get('title', 'Untitled'),
                        'created': data.get('created'),
                        'modified': data.get('modified'),
                        'message_count': len(data.get('messages', [])),
                    }
                except Exception as e:
                    logger.warning(f"Error loading metadata for {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
        
        return conversations

    def rename(self, conversation_id: str, new_title: str) -> bool:
        """Rename conversation."""
        try:
            manager = self.load(conversation_id)
            if not manager:
                return False
            manager.title = new_title
            manager.modified = datetime.now().isoformat()
            return self.save(manager)
        except Exception as e:
            logger.error(f"Error renaming conversation: {e}")
            return False
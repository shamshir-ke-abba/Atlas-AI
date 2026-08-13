"""
Conversation Service
"""

import json
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from config import CONVERSATIONS_DIR

logger = logging.getLogger(__name__)


class ConversationService:
    """Manages conversations."""
    
    def __init__(self):
        self.conversations_dir = CONVERSATIONS_DIR
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        self.current_id: Optional[str] = None
        self.current_messages: List[Dict[str, Any]] = []

    def new(self) -> str:
        """Create new conversation."""
        conv_id = str(uuid.uuid4())
        self.current_id = conv_id
        self.current_messages = []
        
        # Save empty conversation
        self._save_current()
        
        logger.info(f"Created conversation: {conv_id}")
        return conv_id

    def load(self, conversation_id: str) -> bool:
        """Load conversation."""
        try:
            file_path = self._get_path(conversation_id)
            
            if not file_path.exists():
                logger.warning(f"Conversation not found: {conversation_id}")
                return False
            
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_id = conversation_id
            self.current_messages = data.get('messages', [])
            
            logger.info(f"Loaded conversation: {conversation_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading conversation: {e}")
            return False

    def add_user(self, message: str) -> None:
        """Add user message."""
        msg = {
            'sender': 'You',
            'text': message,
            'is_user': True,
            'timestamp': datetime.now().isoformat(),
        }
        self.current_messages.append(msg)

    def add_assistant(self, message: str) -> None:
        """Add assistant message."""
        msg = {
            'sender': 'Atlas',
            'text': message,
            'is_user': False,
            'timestamp': datetime.now().isoformat(),
        }
        self.current_messages.append(msg)

    def save(self) -> bool:
        """Save current conversation."""
        return self._save_current()

    def _save_current(self) -> bool:
        """Save current conversation to disk."""
        try:
            if not self.current_id:
                return False
            
            file_path = self._get_path(self.current_id)
            
            data = {
                'id': self.current_id,
                'title': self._get_title(),
                'created': datetime.now().isoformat(),
                'messages': self.current_messages,
            }
            
            with file_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return False

    def _get_title(self) -> str:
        """Get conversation title from first message."""
        if not self.current_messages:
            return "New Chat"
        
        first_msg = self.current_messages[0].get('text', '')
        return first_msg[:50] + ("..." if len(first_msg) > 50 else "")

    def _get_path(self, conversation_id: str) -> Path:
        """Get file path for conversation."""
        return self.conversations_dir / f"{conversation_id}.json"

    def list(self) -> Dict[str, Dict]:
        """List all conversations."""
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
                        'messages': data.get('messages', []),
                    }
                except Exception as e:
                    logger.warning(f"Error loading {file_path}: {e}")
        
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
        
        return conversations

    def delete(self, conversation_id: str) -> bool:
        """Delete conversation."""
        try:
            file_path = self._get_path(conversation_id)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted conversation: {conversation_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False

    def rename(self, conversation_id: str, new_title: str) -> bool:
        """Rename conversation."""
        try:
            file_path = self._get_path(conversation_id)
            
            if not file_path.exists():
                return False
            
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            
            data['title'] = new_title
            
            with file_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logger.error(f"Error renaming conversation: {e}")
            return False

    def clear(self) -> None:
        """Clear current conversation."""
        self.current_messages = []
        self._save_current()

    def get_id(self) -> Optional[str]:
        """Get current conversation ID."""
        return self.current_id

    def last(self) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return self.current_messages.copy()
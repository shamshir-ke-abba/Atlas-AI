"""
Memory Service - Extract and recall information
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from config import MEMORY_FILE

logger = logging.getLogger(__name__)


class MemoryService:
    """Manages user memory."""
    
    def __init__(self):
        self.memory_file = MEMORY_FILE
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load memory from disk."""
        try:
            if self.memory_file.exists():
                with self.memory_file.open('r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
        
        return {'user': {}, 'facts': {}}

    def _save(self) -> None:
        """Save memory to disk."""
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            
            with self.memory_file.open('w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            logger.error(f"Error saving memory: {e}")

    def extract(self, message: str) -> None:
        """Extract facts from message."""
        # Simple pattern matching for common facts
        message_lower = message.lower()
        
        if "my name is" in message_lower or "i'm" in message_lower or "i am" in message_lower:
            # Try to extract name
            words = message.split()
            for i, word in enumerate(words):
                if word.lower() in ["am", "is", "name"]:
                    if i + 1 < len(words):
                        self.data['user']['name'] = words[i + 1]
                        self._save()

    def try_recall(self, message: str) -> Optional[str]:
        """Try to recall relevant memory."""
        
        if "who am i" in message.lower():
            name = self.data.get('user', {}).get('name')
            if name:
                return f"You are {name}."
        
        if "what is my name" in message.lower():
            name = self.data.get('user', {}).get('name')
            if name:
                return f"Your name is {name}."
        
        return None

    def remember(self, category: str, key: str, value: Any) -> None:
        """Store memory."""
        if category not in self.data:
            self.data[category] = {}
        
        self.data[category][key] = value
        self._save()

    def recall(self, category: str, key: str) -> Optional[Any]:
        """Recall memory."""
        return self.data.get(category, {}).get(key)

    def all(self) -> Dict[str, Any]:
        """Get all memory."""
        return self.data.copy()
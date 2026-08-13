"""
Time Plugin
"""

from datetime import datetime
from plugins.base import AtlasPlugin


class TimePlugin(AtlasPlugin):
    """Current time/date plugin."""
    
    def __init__(self):
        super().__init__()
        self.name = "Time"
        self.icon = "🕐"
        self.enabled = True
        self.triggers = ["time", "date", "what time"]

    def can_handle(self, message: str) -> bool:
        """Check if can handle message."""
        return any(t in message.lower() for t in self.triggers)

    def run(self, *args, **kwargs) -> str:
        """Get current time."""
        now = datetime.now()
        return f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
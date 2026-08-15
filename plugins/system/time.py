"""
Atlas V3 Time Plugin.
"""

from datetime import datetime
from plugins.base import AtlasPlugin


class TimePlugin(AtlasPlugin):
    name = "time"
    display_name = "Time"
    description = "Provides current local time."
    icon = "🕐"
    has_gui = True
    gui_id = "time"
    priority = 10

    triggers = [
        "what time is it",
        "what's the time",
        "what is the time",
        "tell me the time",
        "current time",
        "time now",
        "what time",
        "time please",
        "time",
        "clock",
    ]

    def can_handle(self, message):
        text = str(message or "").lower().strip().rstrip("?!.,")
        return bool(text) and any(
            text == trigger or text.startswith(trigger + " ")
            for trigger in self.triggers
        )

    def run(self, **kwargs):
        return datetime.now().strftime("%I:%M:%S %p")

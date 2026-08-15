"""
Atlas V3 Calendar Plugin.
"""

from datetime import datetime
from plugins.base import AtlasPlugin


class CalendarPlugin(AtlasPlugin):
    name = "calendar"
    display_name = "Calendar"
    description = "Shows the current month, date, day and year."
    icon = "📅"
    has_gui = True
    gui_id = "calendar"
    priority = 15

    triggers = [
        "calendar",
        "date",
        "today",
        "what day is it",
        "what is today's date",
        "what is today",
        "today's date",
        "current date",
        "current day",
    ]

    def can_handle(self, message):
        text = str(message or "").lower().strip().rstrip("?!.,")
        if not text:
            return False
        return any(
            text == trigger or text.startswith(trigger + " ")
            for trigger in self.triggers
        )

    def run(self, **kwargs):
        now = datetime.now()
        return (
            f"{now.strftime('%A, %d %B %Y')} • "
            f"{now.strftime('%I:%M:%S %p')}"
        )

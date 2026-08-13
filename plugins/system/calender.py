"""
Atlas Calendar Plugin
"""

from datetime import datetime

from plugins.base import AtlasPlugin


class CalendarPlugin(AtlasPlugin):

    name = "calendar"

    display_name = "Calendar"

    description = (
        "Provides the current date, day, and calendar information."
    )

    icon = "📅"

    has_gui = False

    triggers = [
        "calendar",
        "date",
        "today",
        "day",
    ]

    # ==================================================
    # Can Handle
    # ==================================================

    def can_handle(
        self,
        message,
    ):

        text = message.lower().strip()

        for trigger in self.triggers:

            if text == trigger:
                return True

            if text.startswith(
                trigger + " "
            ):
                return True

        return False

    # ==================================================
    # Run
    # ==================================================

    def run(
        self,
        **kwargs,
    ):

        now = datetime.now()

        return (
            f"Today is {now.strftime('%A, %d %B %Y')}.\n"
            f"Current date: {now.strftime('%Y-%m-%d')}"
        )
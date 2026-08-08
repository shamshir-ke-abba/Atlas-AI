"""
Time Plugin
"""

from datetime import datetime

from plugins.base import AtlasPlugin


class TimePlugin(AtlasPlugin):

    name = "time"

    description = (
        "Returns the current time."
    )

    triggers = [
        "what time is it",
        "what's the time",
        "what is the time",
        "tell me the time",
        "current time",
        "current time please",
        "time now",
        "what time",
        "time please",
        "time",
        "clock",
    ]

    def can_handle(
        self,
        message,
    ):

        text = (
            message
            .lower()
            .strip()
            .rstrip("?!.")
        )

        for trigger in self.triggers:

            if text == trigger:
                return True

            if text.startswith(
                trigger + " "
            ):
                return True

        return False

    def run(
        self,
        **kwargs,
    ):

        return datetime.now().strftime(
            "%I:%M %p"
        )
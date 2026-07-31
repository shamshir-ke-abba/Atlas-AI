"""
Atlas V3 Event Bus

The Event Bus allows independent components
to communicate without directly referencing
each other.
"""

from collections import defaultdict
from typing import Callable, Type

from core.events import Event


class EventBus:
    """
    Publish/Subscribe event bus.
    """

    def __init__(self):

        self._listeners = defaultdict(list)

    # ------------------------------------------------------
    # Subscribe
    # ------------------------------------------------------

    def subscribe(
        self,
        event_type: Type[Event],
        callback: Callable,
    ):

        if callback not in self._listeners[event_type]:

            self._listeners[event_type].append(
                callback
            )

    # ------------------------------------------------------
    # Unsubscribe
    # ------------------------------------------------------

    def unsubscribe(
        self,
        event_type: Type[Event],
        callback: Callable,
    ):

        if callback in self._listeners[event_type]:

            self._listeners[event_type].remove(
                callback
            )

    # ------------------------------------------------------
    # Publish
    # ------------------------------------------------------

    def publish(self, event: Event):

        for callback in self._listeners[type(event)]:

            callback(event)


# ==========================================================
# Global Event Bus
# ==========================================================

bus = EventBus()
"""
Atlas V3 Controller

The Controller is the kernel of Atlas.

It coordinates communication between
the GUI, AI, memory and tools using
the Event Bus.
"""


from core.services import Service
from core.events import (
    MessageReceived,
    ThinkingStarted,
    ThinkingFinished,
    ChunkReceived,
)

from ai.brain import AtlasBrain
from core.logger import logger


class Controller(Service):

    def __init__(self, bus, state):

        self.bus = bus
        self.state = state

        self.brain = AtlasBrain()

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def start(self):

        logger.info("Starting Controller...")

        self.bus.subscribe(
            MessageReceived,
            self.on_message_received,
        )

    def stop(self):

        logger.info("Stopping Controller...")

        self.bus.unsubscribe(
            MessageReceived,
            self.on_message_received,
        )

    # --------------------------------------------------
    # Event Handlers
    # --------------------------------------------------

    def on_message_received(self, event):

        logger.info(
            f"User: {event.text}"
        )

        self.state.current_message = event.text
        self.state.status = "Thinking"
        self.state.is_generating = True

        self.bus.publish(
            ThinkingStarted()
        )


        response = self.brain.process(
            event.text
        )


        self.bus.publish(
            ChunkReceived(
                response
            )
        )   

        self.bus.publish(
            ThinkingFinished()
        )

        self.state.status = "Ready"
        self.state.is_generating = False
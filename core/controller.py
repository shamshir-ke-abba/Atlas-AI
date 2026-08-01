"""
Atlas V3 Controller

Coordinates communication between
the GUI and backend services.
"""

from core.events import (
    ChunkReceived,
    MessageReceived,
    ThinkingFinished,
    ThinkingStarted,
)

from core.ai_service import AIService
from core.logger import logger


class Controller:

    def __init__(self, bus, state):

        self.bus = bus
        self.state = state

        self.ai = AIService(
            bus,
            state,
        )

        self.ai.chunk_ready.connect(
            self.on_chunk
        )

        self.ai.finished.connect(
            self.on_finished
        )

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def start(self):

        logger.info("Starting Controller...")

        self.bus.subscribe(
            MessageReceived,
            self.on_message_received,
        )

        self.ai.start()

    def stop(self):

        logger.info("Stopping Controller...")

        self.bus.unsubscribe(
            MessageReceived,
            self.on_message_received,
        )

        self.ai.stop()

    # --------------------------------------------------
    # Events
    # --------------------------------------------------

    def on_message_received(
        self,
        event,
    ):

        self.state.current_message = event.text
        self.state.status = "Thinking"
        self.state.is_generating = True

        self.bus.publish(
            ThinkingStarted()
        )

        self.ai.generate(
            event.text
        )

    def on_chunk(
        self,
        text,
    ):

        self.bus.publish(
            ChunkReceived(
                text
            )
        )

    def on_finished(
        self,
    ):

        self.state.status = "Ready"
        self.state.is_generating = False

        self.bus.publish(
            ThinkingFinished()
        )
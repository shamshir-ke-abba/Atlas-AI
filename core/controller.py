"""
Atlas V3 Controller

Coordinates communication between
the GUI and backend services.
"""

from PySide6.QtCore import QObject, Slot
from core.signals import ControllerSignals
from core.events import (
    ChunkReceived,
    MessageReceived,
    ThinkingFinished,
    ThinkingStarted,
)
from core.ai_service import AIService
from core.logger import logger


class Controller(QObject):

    def __init__(self, bus, state):

        super().__init__()

        self.bus = bus
        self.state = state

        self.ai = AIService(
            bus,
            state,
        )

        self.ai.response_ready.connect(
            self.on_ai_response
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
    # Event Handlers
    # --------------------------------------------------

    def on_message_received(
        self,
        event,
    ):

        logger.info(
            f"User: {event.text}"
        )

        self.state.current_message = event.text
        self.state.status = "Thinking"
        self.state.is_generating = True

        self.bus.publish(
            ThinkingStarted()
        )

        self.ai.generate(
            event.text
        )

    @Slot(str)
    def on_ai_response(
        self,
        response,
    ):

        self.bus.publish(
            ChunkReceived(
                response
            )
        )

        self.state.status = "Ready"
        self.state.is_generating = False

        self.bus.publish(
            ThinkingFinished()
        )
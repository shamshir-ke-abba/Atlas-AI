"""
Atlas V3 Controller

Coordinates communication between
the GUI, Web API and backend services.
"""

from core.ai_service import AIService
from core.events import (
    ChunkReceived,
    ConversationCleared,
    MessageReceived,
    ThinkingFinished,
    ThinkingStarted,
)
from core.logger import logger


class Controller:

    def __init__(
        self,
        bus,
        state,
    ):

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

    # ==================================================
    # Lifecycle
    # ==================================================

    def start(self):

        logger.info(
            "Starting Controller..."
        )

        self.bus.subscribe(
            MessageReceived,
            self.on_message_received,
        )

        self.bus.subscribe(
            ConversationCleared,
            self.on_conversation_cleared,
        )

        self.ai.start()

    def stop(self):

        logger.info(
            "Stopping Controller..."
        )

        self.bus.unsubscribe(
            MessageReceived,
            self.on_message_received,
        )

        self.bus.unsubscribe(
            ConversationCleared,
            self.on_conversation_cleared,
        )

        self.ai.stop()

    # ==================================================
    # Synchronous API
    # ==================================================

    def chat(
        self,
        message,
    ):

        response = ""

        for chunk in self.ai.worker.brain.process(
            message
        ):

            response += chunk

        return response

    # ==================================================
    # Streaming API
    # ==================================================

    def stream_chat(
        self,
        message,
    ):

        yield from self.ai.worker.brain.process(
            message
        )

    # ==================================================
    # Conversation API
    # ==================================================

    def list_conversations(self):

        return self.ai.worker.brain.list_conversations()

    def load_conversation(
        self,
        conversation_id,
    ):

        return self.ai.worker.brain.load_conversation(
            conversation_id
        )

    def delete_conversation(
        self,
        conversation_id,
    ):

        return self.ai.worker.brain.delete_conversation(
            conversation_id
        )

    # ==================================================
    # Event Handlers
    # ==================================================

    def on_message_received(
        self,
        event,
    ):

        self.state.current_message = event.text
        self.state.current_response = ""
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

        self.state.current_response += text

        self.bus.publish(
            ChunkReceived(text)
        )

    def on_finished(
        self,
    ):

        self.state.status = "Ready"
        self.state.is_generating = False

        self.bus.publish(
            ThinkingFinished()
        )

    def on_conversation_cleared(
        self,
        event,
    ):

        self.ai.worker.brain.clear_conversation()

        self.state.current_message = ""
        self.state.current_response = ""

        logger.info(
            "Conversation cleared."
        )
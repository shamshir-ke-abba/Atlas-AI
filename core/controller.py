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

        self._sync_active_conversation()

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

        self._sync_active_conversation()

        return response

    # ==================================================
    # Streaming API
    # ==================================================

    def stream_chat(
        self,
        message,
    ):

        for chunk in self.ai.worker.brain.process(
            message
        ):

            yield chunk

        self._sync_active_conversation()

    # ==================================================
    # Conversation API
    # ==================================================

    def new_conversation(self):

        conversation_id = (
            self.ai.worker.brain.new_conversation()
        )

        self.state.active_conversation_id = (
            conversation_id
        )

        self.state.current_message = ""
        self.state.current_response = ""
        self.state.status = "Ready"
        self.state.is_generating = False

        logger.info(
            f"New conversation created: "
            f"{conversation_id}"
        )

        return conversation_id

    def load_conversation(
        self,
        conversation_id,
    ):

        success = (
            self.ai.worker.brain.load_conversation(
                conversation_id
            )
        )

        if not success:

            logger.warning(
                f"Failed to load conversation: "
                f"{conversation_id}"
            )

            return False

        self.state.active_conversation_id = (
            self.ai.worker.brain.get_active_conversation_id()
        )

        self.state.current_message = ""
        self.state.current_response = ""
        self.state.status = "Ready"
        self.state.is_generating = False

        logger.info(
            f"Conversation loaded: "
            f"{conversation_id}"
        )

        return True

    def get_active_conversation(self):

        return self.ai.worker.brain.conversation

    def delete_conversation(
        self,
        conversation_id,
    ):

        success = (
            self.ai.worker.brain.delete_conversation(
                conversation_id
            )
        )

        if success:

            self._sync_active_conversation()

            logger.info(
                f"Conversation deleted: "
                f"{conversation_id}"
            )

        return success

    def rename_conversation(
        self,
        conversation_id,
        title,
    ):

        success = (
            self.ai.worker.brain.rename_conversation(
                conversation_id,
                title,
            )
        )

        if success:

            logger.info(
                f"Conversation renamed: "
                f"{conversation_id}"
            )

        return success

    def list_conversations(self):

        return (
            self.ai.worker.brain.list_conversations()
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
            ChunkReceived(
                text
            )
        )

    def on_finished(
        self,
    ):

        self.state.status = "Ready"
        self.state.is_generating = False

        self._sync_active_conversation()

        self.bus.publish(
            ThinkingFinished()
        )

    def on_conversation_cleared(
        self,
        event,
    ):

        conversation_id = (
            self.new_conversation()
        )

        logger.info(
            f"Conversation cleared. "
            f"Active conversation: "
            f"{conversation_id}"
        )

    # ==================================================
    # Internal
    # ==================================================

    def _sync_active_conversation(
        self,
    ):

        brain = self.ai.worker.brain

        self.state.active_conversation_id = (
            brain.get_active_conversation_id()
        )
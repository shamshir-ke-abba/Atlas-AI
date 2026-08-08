"""
Atlas Brain

Coordinates memory, context,
conversation and the model.
"""

from ai.model import AtlasModel
from ai.context_builder import ContextBuilder
from ai.memory_patterns import PATTERNS
from ai.planner import Planner
from ai.translator import LanguageTranslator

from core.memory import MemoryManager
from core.tool_manager import ToolManager
from core.conversation import ConversationManager
from core.conversation_store import ConversationStore
from core.intent import IntentRouter


class AtlasBrain:

    def __init__(self):

        self.model = AtlasModel()

        self.memory = MemoryManager()

        self.tools = ToolManager()

        self.context = ContextBuilder()

        self.conversation = ConversationManager()

        self.conversation_store = ConversationStore()

        self.router = IntentRouter(
            self.tools.plugins.plugins
        )

        self.planner = Planner(
            self.router
        )

    # ==================================================
    # Conversation Persistence
    # ==================================================

    def save_conversation(self):

        if not self.conversation.history():
            return

        self.conversation_store.save(
            self.conversation
        )

    def clear_conversation(self):

        self.save_conversation()

        self.conversation.new_conversation()

    # ==================================================
    # Conversation Management
    # ==================================================

    def list_conversations(self):

        return self.conversation_store.list_conversations()

    def load_conversation(
        self,
        conversation_id,
    ):

        data = self.conversation_store.load(
            conversation_id
        )

        if data is None:
            return False

        self.conversation.load(
            data
        )

        return True

    def delete_conversation(
        self,
        conversation_id,
    ):

        return self.conversation_store.delete(
            conversation_id
        )

    # ==================================================
    # Processing
    # ==================================================

    def process(
        self,
        message,
    ):

        text = message.lower()

        # ----------------------------------
        # Hinglish Detection
        # ----------------------------------

        is_hinglish = LanguageTranslator.is_hinglish(message)

        # ----------------------------------
        # Conversation
        # ----------------------------------

        self.conversation.add_user(
            message
        )

        # ----------------------------------
        # Automatic Title
        # ----------------------------------

        if (
            self.conversation.get_title()
            == "New Chat"
        ):

            title = message.strip()

            if len(title) > 40:

                title = (
                    title[:40].rstrip()
                    + "..."
                )

            self.conversation.set_title(
                title
            )

        # ----------------------------------
        # Memory Extraction
        # ----------------------------------

        for phrase, category, key in PATTERNS:

            if phrase in text:

                index = text.find(
                    phrase
                )

                value = message[
                    index + len(phrase):
                ].strip()

                self.memory.remember(
                    category,
                    key,
                    value,
                )

                break

        # ----------------------------------
        # Memory Recall
        # ----------------------------------

        # Special handling for questions about AI
        ai_identity_triggers = [
            "tera naam",  # Your name (in Hindi)
            "tumhara naam",  # Your name
            "what is your name",
            "whats your name",
            "who are you",
            "what are you called",
            "tum kaun ho",  # Who are you (Hindi)
        ]

        for trigger in ai_identity_triggers:
            if trigger in text:
                response = "I'm Atlas, an AI assistant created by Saad."
                self.conversation.add_assistant(response)
                self.save_conversation()
                yield response
                return

        # User's memory recall
        recall = {

            "what's my name": (
                "identity",
                "name",
            ),

            "what is my name": (
                "identity",
                "name",
            ),

            "who am i": (
                "identity",
                "name",
            ),

            "mera naam": (
                "identity",
                "name",
            ),

            "mera naam kya": (
                "identity",
                "name",
            ),

            "main kaun hoon": (
                "identity",
                "name",
            ),

            "where do i live": (
                "identity",
                "city",
            ),

            "what city do i live in": (
                "identity",
                "city",
            ),

            "main kaha rhata": (
                "identity",
                "city",
            ),

            "mera ghar": (
                "identity",
                "city",
            ),
        }

        for trigger, memory in recall.items():

            if trigger in text:

                value = self.memory.recall(
                    memory[0],
                    memory[1],
                )

                if value:

                    self.conversation.add_assistant(
                        value
                    )

                    self.save_conversation()

                    yield value

                else:

                    response = "I don't know."

                    self.conversation.add_assistant(
                        response
                    )

                    self.save_conversation()

                    yield response

                return

        # ----------------------------------
        # Planning
        # ----------------------------------

        plan = self.planner.plan(
            message
        )

        # ----------------------------------
        # Tool Execution
        # ----------------------------------

        if plan.action == Planner.TOOL:

            plugin = plan.plugin

            result = self.tools.execute(
                plugin.name,
                expression=plan.arguments,
            )

            self.conversation.add_assistant(
                result
            )

            self.save_conversation()

            yield result

            return

        # ----------------------------------
        # Build Context
        # ----------------------------------

        context = self.context.build(
            self.conversation.last(),
            message,
            is_hinglish=is_hinglish,
        )

        # ----------------------------------
        # Model
        # ----------------------------------

        reply = ""

        for chunk in self.model.generate(
            context,
        ):

            reply += chunk

            yield chunk

        self.conversation.add_assistant(
            reply
        )

        self.save_conversation()
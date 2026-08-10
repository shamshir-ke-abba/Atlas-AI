"""
Atlas Brain

Coordinates memory, context,
conversation, tools, knowledge routing,
and the local model.
"""

from ai.model import AtlasModel
from ai.context_builder import ContextBuilder
from ai.memory_patterns import PATTERNS
from ai.planner import Planner
from ai.knowledge_decider import (
    KnowledgeDecider,
    Decision,
)

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

        self.knowledge_decider = KnowledgeDecider()

    # ==================================================
    # Conversation
    # ==================================================

    def clear_conversation(self):

        self.conversation = ConversationManager()

    def new_conversation(self):

        self._save_current_conversation()

        self.conversation = ConversationManager()

        return self.conversation.get_id()

    def load_conversation(
        self,
        conversation_id,
    ):

        self._save_current_conversation()

        data = self.conversation_store.load(
            conversation_id
        )

        if data is None:
            return False

        if isinstance(
            data,
            ConversationManager,
        ):

            self.conversation = data

        elif isinstance(
            data,
            dict,
        ):

            conversation = ConversationManager()

            conversation.load(data)

            self.conversation = conversation

        else:

            return False

        return True

    def list_conversations(self):

        return (
            self.conversation_store
            .list_conversations()
        )

    def delete_conversation(
        self,
        conversation_id,
    ):

        deleted = (
            self.conversation_store.delete(
                conversation_id
            )
        )

        if not deleted:
            return False

        if (
            conversation_id
            == self.conversation.get_id()
        ):

            self.conversation = (
                ConversationManager()
            )

        return True

    def rename_conversation(
        self,
        conversation_id,
        title,
    ):

        title = title.strip()

        if not title:
            return False

        data = self.conversation_store.load(
            conversation_id
        )

        if data is None:
            return False

        if isinstance(
            data,
            ConversationManager,
        ):

            conversation = data

        elif isinstance(
            data,
            dict,
        ):

            conversation = ConversationManager()

            conversation.load(data)

        else:

            return False

        conversation.set_title(title)

        self.conversation_store.save(
            conversation
        )

        if (
            conversation_id
            == self.conversation.get_id()
        ):

            self.conversation.set_title(title)

        return True

    def get_active_conversation_id(self):

        return self.conversation.get_id()

    # ==================================================
    # Processing
    # ==================================================

    def process(
        self,
        message,
    ):

        text = message.lower()

        self.conversation.add_user(message)

        self._auto_title(message)

        # ==================================================
        # Memory Extraction
        # ==================================================

        for phrase, category, key in PATTERNS:

            if phrase in text:

                index = text.find(phrase)

                value = message[
                    index + len(phrase):
                ].strip()

                self.memory.remember(
                    category,
                    key,
                    value,
                )

                break

        # ==================================================
        # Memory Recall
        # ==================================================

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

            "where do i live": (
                "identity",
                "city",
            ),

            "what city do i live in": (
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

                    self._save_current_conversation()

                    yield value

                else:

                    response = "I don't know."

                    self.conversation.add_assistant(
                        response
                    )

                    self._save_current_conversation()

                    yield response

                return

        # ==================================================
        # Knowledge Decision
        # ==================================================

        decision = (
            self.knowledge_decider.decide(
                message
            )
        )

        # ==================================================
        # WEB
        # ==================================================

        if decision.decision == Decision.WEB:

            web_result = self._web_search(message)

            context = self._build_web_prompt(
                message,
                web_result,
                both=False,
            )

            yield from self._generate_and_save(
                context
            )

            return

        # ==================================================
        # BOTH
        # ==================================================

        if decision.decision == Decision.BOTH:

            web_result = self._web_search(message)

            context = self._build_web_prompt(
                message,
                web_result,
                both=True,
            )

            yield from self._generate_and_save(
                context
            )

            return

        # ==================================================
        # LOCAL
        # ==================================================

        plan = self.planner.plan(message)

        if plan.action == Planner.TOOL:

            plugin = plan.plugin

            result = self.tools.execute(
                plugin.name,
                expression=plan.arguments,
            )

            self.conversation.add_assistant(result)

            self._save_current_conversation()

            yield result

            return

        context = self.context.build(
            self.conversation.last(),
            message,
        )

        yield from self._generate_and_save(context)

    # ==================================================
    # Web Search
    # ==================================================

    def _web_search(
        self,
        question,
    ):

        try:

            return self.tools.execute(
                "web_search",
                expression=question,
            )

        except Exception as error:

            return (
                "Web search failed: "
                + str(error)
            )

    # ==================================================
    # Web Prompt
    # ==================================================

    def _build_web_prompt(
        self,
        question,
        web_result,
        both=False,
    ):

        if both:

            return f"""
SYSTEM:
You are Atlas. Answer the user using the
WEB RESULTS supplied below.

The web search has ALREADY happened.
The text below is the search result.

You do NOT need internet access.
You do NOT need to perform a search.

USER:
{question}

WEB RESULTS:
{web_result}

TASK:
Read the WEB RESULTS and answer the USER.

Use the information in WEB RESULTS as evidence.

If the results do not contain enough information,
say that the search results are insufficient.

Do not say you cannot access the web.
Do not say you cannot browse.
Do not say you cannot perform searches.
Do not talk about your training data.
Do not talk about internal routing.

Give the answer directly.
"""

        return f"""
SYSTEM:
You are Atlas. Answer the user using the
WEB RESULTS supplied below.

The web search has ALREADY happened.

USER:
{question}

WEB RESULTS:
{web_result}

TASK:
Answer the user's question using the supplied
WEB RESULTS.

Do not say you cannot access the web.
Do not say you cannot browse.
Do not say you cannot perform searches.

If the results are insufficient, say so.

Give the answer directly.
"""

    # ==================================================
    # Generate + Save
    # ==================================================

    def _generate_and_save(
        self,
        context,
    ):

        reply = ""

        for chunk in self.model.generate(context):

            reply += chunk

            yield chunk

        self.conversation.add_assistant(reply)

        self._save_current_conversation()

    # ==================================================
    # Automatic Title
    # ==================================================

    def _auto_title(
        self,
        message,
    ):

        if (
            self.conversation.get_title()
            != "New Chat"
        ):

            return

        text = " ".join(
            message.strip().split()
        )

        if not text:
            return

        words = text.split()

        if len(words) > 7:

            title = (
                " ".join(words[:7])
                + "..."
            )

        else:

            title = text

        self.conversation.set_title(title)

    # ==================================================
    # Internal Persistence
    # ==================================================

    def _save_current_conversation(self):

        if not self.conversation.history():

            return

        self.conversation_store.save(
            self.conversation
        )
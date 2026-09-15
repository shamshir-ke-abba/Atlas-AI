"""
Atlas V3 Browser Runtime

Headless runtime for the LAN/browser interface.
Uses the same Brain, Ollama model, ToolManager and persistent
ConversationService as Atlas without constructing the Qt GUI.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any, Dict, Optional

from ai.brain import AtlasBrain
from ai.model import AtlasModel
from core.tool_manager import ToolManager
from core.memory import MemoryManager
from ai.services.conversation_service import ConversationService
from config import MODEL_NAME, OLLAMA_HOST


@dataclass
class WebSession:
    conversation: ConversationService
    brain: AtlasBrain
    lock: RLock


class WebAtlasRuntime:
    def __init__(self):
        self._sessions: Dict[str, WebSession] = {}
        self._sessions_lock = RLock()

        self.tools = ToolManager()
        self.model = AtlasModel()
        self.catalog = ConversationService()
        self.memory = MemoryManager()

    def session(self, session_id: str) -> WebSession:
        session_id = str(session_id).strip()
        if not session_id:
            raise ValueError("session_id is required")

        with self._sessions_lock:
            existing = self._sessions.get(session_id)
            if existing is not None:
                return existing

            conversation = ConversationService()
            conversation_id = conversation.new()

            brain = AtlasBrain(
                model=self.model,
                memory=self.memory,
                tools=self.tools,
            )

            session = WebSession(
                conversation=conversation,
                brain=brain,
                lock=RLock(),
            )

            session.conversation.load(conversation_id)
            brain.set_conversation_history(
                session.conversation.history()
            )

            self._sessions[session_id] = session
            return session

    def ensure_conversation(
        self,
        session_id: str,
        conversation_id: Optional[str] = None,
    ) -> WebSession:
        session = self.session(session_id)

        if conversation_id:
            conversation_id = str(conversation_id)

            if session.conversation.current_id != conversation_id:
                if not session.conversation.load(conversation_id):
                    raise ValueError("Conversation not found.")

                session.brain.set_conversation_history(
                    session.conversation.history()
                )

        return session

    def conversations(self):
        return self.catalog.list()

    def create_conversation(self, session_id: str):
        session = self.session(session_id)

        with session.lock:
            conversation_id = session.conversation.new()
            session.brain.set_conversation_history([])
            return conversation_id

    def load_conversation(
        self,
        session_id: str,
        conversation_id: str,
    ):
        session = self.session(session_id)

        with session.lock:
            if not session.conversation.load(conversation_id):
                raise ValueError("Conversation not found.")

            session.brain.set_conversation_history(
                session.conversation.history()
            )

            return session.conversation.history()

    def delete_conversation(
        self,
        session_id: str,
        conversation_id: str,
    ):
        session = self.session(session_id)

        with session.lock:
            ok = session.conversation.delete(conversation_id)

            if (
                ok
                and session.conversation.current_id == conversation_id
            ):
                new_id = session.conversation.new()
                session.brain.set_conversation_history([])
                return new_id

            return None

    def execute_tool(
        self,
        session_id: str,
        tool_name: str,
        action: str = "",
        expression: str = "",
        arguments: Optional[Dict[str, Any]] = None,
    ):
        """Execute a tool directly from the browser Tool Workspace."""

        tool_name = str(tool_name or "").strip().lower()
        if not tool_name:
            raise ValueError("Tool name is required.")

        arguments = dict(arguments or {})

        if action:
            arguments["action"] = action

        if expression:
            arguments["expression"] = expression

        # Some plugins expect expression while others accept named kwargs.
        # The ToolManager/PluginManager layer handles the actual dispatch.
        result = self.tools.execute(
            tool_name,
            **arguments,
        )

        return {
            "tool": tool_name,
            "result": str(result),
        }

    def status(self, session_id: str):
        session = self.session(session_id)

        try:
            tool_status = self.tools.status()
        except Exception:
            tool_status = {
                "total": 0,
                "enabled": 0,
                "disabled": 0,
                "tools": [],
            }

        return {
            "model": MODEL_NAME,
            "ollama": OLLAMA_HOST,
            "conversation_id": session.conversation.current_id,
            "conversation_title": session.conversation.current_title,
            "history_messages": len(session.conversation.history()),
            "tools": tool_status,
            "web_search": True,
        }

    def chat_stream(
        self,
        session_id: str,
        message: str,
        conversation_id: Optional[str] = None,
    ):
        session = self.ensure_conversation(
            session_id,
            conversation_id,
        )

        with session.lock:
            session.conversation.add_user(message)
            session.conversation.save()

            history_before = session.conversation.history()[:-1]
            session.brain.set_conversation_history(history_before)

            full_response = []

            try:
                for chunk in session.brain.stream_message(
                    message,
                    conversation_history=history_before,
                ):
                    text = str(chunk)
                    full_response.append(text)

                    yield {
                        "type": "chunk",
                        "text": text,
                    }

                response = "".join(full_response).strip()

                if response:
                    session.conversation.add_assistant(response)
                    session.conversation.save()

                session.brain.set_conversation_history(
                    session.conversation.history()
                )

                yield {
                    "type": "done",
                    "conversation_id": session.conversation.current_id,
                    "title": session.conversation.current_title,
                    "web": {
                        "query": getattr(
                            session.brain,
                            "last_web_query",
                            None,
                        ),
                        "sources": getattr(
                            session.brain,
                            "last_web_sources",
                            [],
                        ),
                    },
                }

            except Exception as exc:
                yield {
                    "type": "error",
                    "message": str(exc),
                }

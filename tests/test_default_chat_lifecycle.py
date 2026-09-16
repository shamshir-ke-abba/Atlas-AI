"""Regression test for default chat, new chat, and history lifecycle."""

import tempfile
from pathlib import Path
from PySide6.QtWidgets import QApplication

from core.bus import EventBus
from core.state import AtlasState
from core.controller import Controller
from core.conversation import ConversationStore, ConversationManager


def test_default_chat_lifecycle():
    app = QApplication.instance() or QApplication([])

    with tempfile.TemporaryDirectory() as tmpdir:
        conv_dir = Path(tmpdir) / "conversations"
        conv_dir.mkdir(parents=True)

        # 1. Existing populated conversation from a past session
        cs = ConversationStore()
        cs.conversations_dir = conv_dir
        prior_conv = ConversationManager("past-session-uuid", "Past Discussion")
        prior_conv.add_message("User", "What is quantum entanglement?", is_user=True)
        prior_conv.add_message("Atlas", "Entanglement is...", is_user=False)
        cs.save(prior_conv)

        # 2. Boot controller with this store
        bus = EventBus()
        state = AtlasState()
        ctrl = Controller(bus, state)
        ctrl.conversations = cs
        ctrl.state.active_conversation_id = None
        ctrl._ensure_active_conversation()

        boot_id = ctrl.get_active_conversation_id()
        assert boot_id is not None
        assert boot_id != "past-session-uuid", "Startup must NOT hijack old populated conversation!"

        active = ctrl.get_active_conversation()
        assert active.title == "New Chat"
        assert len(active.get_messages()) == 0

        # 3. User types first message without clicking New Chat
        class MessageEvent:
            text = "Explain the Theory of Relativity"

        ctrl._handle_message_received(MessageEvent())

        active_after = ctrl.get_active_conversation()
        assert active_after.id == boot_id
        assert active_after.title != "New Chat"
        assert "Relativity" in active_after.title or "Explain" in active_after.title
        assert len(active_after.get_messages()) == 1
        assert active_after.get_messages()[0]["text"] == "Explain the Theory of Relativity"

        # Past conversation must remain completely intact
        past_reloaded = cs.load("past-session-uuid")
        assert len(past_reloaded.get_messages()) == 2
        assert past_reloaded.title == "Past Discussion"

        # 4. User clicks New Chat
        new_id = ctrl.create_conversation()
        assert new_id != boot_id
        assert new_id != "past-session-uuid"
        assert ctrl.get_active_conversation_id() == new_id

        # 5. User clicks New Chat again while current conversation is empty
        second_id = ctrl.create_conversation()
        assert second_id == new_id, "Untouched empty New Chat should be reused!"

        # 6. User reopens old conversation
        loaded = ctrl.load_conversation("past-session-uuid")
        assert loaded is True
        assert ctrl.get_active_conversation_id() == "past-session-uuid"
        assert len(ctrl.get_active_conversation().get_messages()) == 2

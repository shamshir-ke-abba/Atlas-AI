"""Tests for streaming, cooperative cancellation, and generation ownership."""

import time
import uuid
import pytest
from PySide6.QtWidgets import QApplication

from core.bus import EventBus
from core.controller import Controller
from core.events import (
    ChunkReceived,
    ErrorOccurred,
    MessageReceived,
    ThinkingFinished,
    ThinkingStarted,
)
from core.state import AtlasState
from gui.widgets.chat import AtlasChat


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def test_setup(qapp):
    bus = EventBus()
    state = AtlasState()
    controller = Controller(bus, state)
    chat = AtlasChat(bus, controller)

    # Mock brain.stream_message to emit controlled chunks without blocking on external Ollama
    def mock_stream(message, conversation_history=None):
        for i in range(5):
            time.sleep(0.01)
            yield f"token{i}_{message} "

    controller.ai.worker.brain.stream_message = mock_stream

    yield bus, state, controller, chat
    try:
        controller.ai.stop()
    except Exception:
        pass


def test_stop_generation_resets_state_and_emits_finished(test_setup):
    bus, state, controller, chat = test_setup

    finished_events = []
    bus.subscribe(ThinkingFinished, lambda ev: finished_events.append(ev))

    # Send Prompt A
    chat.handle_message("Prompt A")
    assert state.is_generating is True
    assert state.active_generation_id is not None
    gen_id_a = state.active_generation_id
    assert chat.is_generating is True
    assert chat.active_generation_id == gen_id_a

    # User clicks stop
    chat.handle_stop_requested()

    # Verify immediate state reset
    assert state.is_generating is False
    assert state.active_generation_id is None
    assert state.status == "Idle"
    assert chat.is_generating is False
    assert chat.active_generation_id is None
    assert chat.input_bar._generating is False
    assert len(finished_events) >= 1
    assert finished_events[-1].generation_id == gen_id_a


def test_prompt_b_immediately_after_stop_works(test_setup):
    bus, state, controller, chat = test_setup

    # 1. Send prompt A
    chat.handle_message("Prompt A")
    gen_id_a = state.active_generation_id
    assert gen_id_a is not None

    # 2. Press stop
    chat.handle_stop_requested()
    assert chat.is_generating is False

    # 3. Immediately send prompt B
    chat.handle_message("Prompt B")

    # Prompt B must NOT be ignored!
    assert state.is_generating is True
    assert state.active_generation_id is not None
    gen_id_b = state.active_generation_id
    assert gen_id_b != gen_id_a
    assert chat.is_generating is True
    assert chat.active_generation_id == gen_id_b
    assert chat.input_bar._generating is True


def test_stale_chunks_from_cancelled_generation_are_dropped(test_setup):
    bus, state, controller, chat = test_setup

    # Start generation A
    chat.handle_message("Prompt A")
    gen_id_a = state.active_generation_id

    # Simulate valid chunk for A
    controller._handle_ai_chunk("Chunk A1", generation_id=gen_id_a)
    assert "Chunk A1" in state.current_response
    assert "Chunk A1" in chat.current_ai_response

    # Stop generation A
    chat.handle_stop_requested()

    # Simulate late chunk from generation A after Stop
    controller._handle_ai_chunk("Chunk A2 late", generation_id=gen_id_a)

    # Chunk A2 must NOT be in state or chat
    assert "Chunk A2 late" not in state.current_response
    assert "Chunk A2 late" not in chat.current_ai_response

    # Now start prompt B
    chat.handle_message("Prompt B")
    gen_id_b = state.active_generation_id
    assert gen_id_b != gen_id_a

    # Another late chunk from A arrives while B is generating
    controller._handle_ai_chunk("Chunk A3 late", generation_id=gen_id_a)
    assert "Chunk A3 late" not in state.current_response
    assert "Chunk A3 late" not in chat.current_ai_response

    # Valid chunk for B arrives
    controller._handle_ai_chunk("Chunk B1", generation_id=gen_id_b)
    assert "Chunk B1" in state.current_response
    assert "Chunk B1" in chat.current_ai_response
    assert "Chunk A" not in chat.current_ai_response


def test_stale_finished_signal_does_not_interrupt_active_generation(test_setup):
    bus, state, controller, chat = test_setup

    # Start generation A
    chat.handle_message("Prompt A")
    gen_id_a = state.active_generation_id

    # Stop A and start B
    chat.handle_stop_requested()
    chat.handle_message("Prompt B")
    gen_id_b = state.active_generation_id

    # Late finished signal from A arrives
    controller._handle_ai_finished(generation_id=gen_id_a)

    # Generation B must STILL be generating!
    assert state.is_generating is True
    assert state.active_generation_id == gen_id_b
    assert chat.is_generating is True

    # Now B finishes
    controller._handle_ai_finished(generation_id=gen_id_b)
    assert state.is_generating is False
    assert state.active_generation_id is None
    assert chat.is_generating is False


def test_rapid_cancel_restart_sequence(test_setup):
    bus, state, controller, chat = test_setup

    # Start 1 -> Stop 1
    chat.handle_message("Turn 1")
    g1 = state.active_generation_id
    chat.handle_stop_requested()
    assert state.is_generating is False

    # Start 2 -> Stop 2
    chat.handle_message("Turn 2")
    g2 = state.active_generation_id
    assert g2 != g1
    chat.handle_stop_requested()
    assert state.is_generating is False

    # Start 3 -> Stream -> Finish
    chat.handle_message("Turn 3")
    g3 = state.active_generation_id
    assert g3 not in (g1, g2)
    assert state.is_generating is True

    controller._handle_ai_chunk("Turn 3 response", generation_id=g3)
    controller._handle_ai_finished(generation_id=g3)

    assert state.is_generating is False
    assert chat.is_generating is False
    assert chat.current_ai_response == "Turn 3 response"


def test_stream_error_cleanup(test_setup):
    bus, state, controller, chat = test_setup

    chat.handle_message("Prompt with error")
    gen_id = state.active_generation_id

    controller._handle_ai_error("Simulated network timeout", generation_id=gen_id)

    assert state.is_generating is False
    assert state.status == "Error"
    assert chat.is_generating is False
    assert chat.input_bar._generating is False


def test_live_threaded_cancellation_and_immediate_prompt_b(test_setup, qapp):
    bus, state, controller, chat = test_setup

    def slow_stream(message, conversation_history=None):
        for i in range(20):
            time.sleep(0.02)
            yield f"tok_{message}_{i} "

    controller.ai.worker.brain.stream_message = slow_stream
    controller.ai.start()

    # 1. Send Prompt A
    chat.handle_message("Alpha")
    gen_a = state.active_generation_id
    assert gen_a is not None

    # Wait for at least one chunk to arrive on main thread
    for _ in range(50):
        qapp.processEvents()
        if chat.current_ai_response:
            break
        time.sleep(0.01)

    assert "tok_Alpha" in chat.current_ai_response

    # 2. User presses Stop while Alpha is actively streaming
    chat.handle_stop_requested()
    assert state.is_generating is False
    assert chat.is_generating is False

    # 3. User immediately submits Prompt B
    chat.handle_message("Beta")
    gen_b = state.active_generation_id
    assert gen_b != gen_a
    assert state.is_generating is True

    # 4. Wait for Prompt B to finish generating
    for _ in range(150):
        qapp.processEvents()
        if not state.is_generating:
            break
        time.sleep(0.01)

    assert state.is_generating is False
    assert "tok_Beta" in chat.current_ai_response
    assert "tok_Alpha" not in chat.current_ai_response


"""Atlas V3 - P3 Snake Game Unit and Integration Tests.

Validates:
1. Snake state machine (IDLE -> PLAYING -> PAUSED -> GAME_OVER -> restart)
2. Controls (Arrow keys, WASD, Space, R, mouse)
3. Grid collisions (wall & self)
4. Unfocus auto-pause
5. Independence from AI state events in AtlasStatusBar
"""

import os
import pytest

# Ensure headless Qt offscreen platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFocusEvent, QKeyEvent
from PySide6.QtWidgets import QApplication

from core.bus import EventBus
from core.events import ChunkReceived, ErrorOccurred, ThinkingFinished, ThinkingStarted
from gui.widgets.snake import (
    GRID_COLS,
    GRID_ROWS,
    STATE_GAME_OVER,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_PLAYING,
    AtlasSnakeCard,
    SnakeCanvas,
)
from gui.widgets.statusbar import AtlasStatusBar


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_snake_initial_state(qapp):
    canvas = SnakeCanvas()
    assert canvas.state == STATE_IDLE
    assert not canvas._timer.isActive()
    assert canvas.score == 0
    assert canvas.high_score == 0
    assert len(canvas.snake) == 3
    assert 0 <= canvas.food[0] < GRID_COLS
    assert 0 <= canvas.food[1] < GRID_ROWS


def test_snake_start_and_pause_transitions(qapp):
    canvas = SnakeCanvas()

    # Start game
    canvas.start_game()
    assert canvas.state == STATE_PLAYING
    assert canvas._timer.isActive()

    # Pause
    canvas.pause_game()
    assert canvas.state == STATE_PAUSED
    assert not canvas._timer.isActive()

    # Resume
    canvas.resume_game()
    assert canvas.state == STATE_PLAYING
    assert canvas._timer.isActive()

    # Toggle pause
    canvas.toggle_pause()
    assert canvas.state == STATE_PAUSED
    canvas.toggle_pause()
    assert canvas.state == STATE_PLAYING


def test_snake_unfocus_autopause(qapp):
    canvas = SnakeCanvas()
    canvas.start_game()
    assert canvas.state == STATE_PLAYING

    # Simulate focus loss
    event = QFocusEvent(QEvent.FocusOut)
    canvas.focusOutEvent(event)

    assert canvas.state == STATE_PAUSED
    assert not canvas._timer.isActive()


def test_snake_controls_arrows_and_wasd(qapp):
    canvas = SnakeCanvas()
    canvas.start_game()

    # Moving right (1, 0)
    assert canvas.direction == (1, 0)

    # Press Down
    event_down = QKeyEvent(QEvent.KeyPress, Qt.Key_Down, Qt.NoModifier)
    canvas.keyPressEvent(event_down)
    assert canvas.next_direction == (0, 1)

    # Tick advances direction to Down (0, 1)
    canvas._tick()
    assert canvas.direction == (0, 1)

    # Now turning Left via 'A' key is a 90-degree turn
    event_a = QKeyEvent(QEvent.KeyPress, Qt.Key_A, Qt.NoModifier)
    canvas.keyPressEvent(event_a)
    assert canvas.next_direction == (-1, 0)

    # Tick advances direction to Left (-1, 0)
    canvas._tick()
    assert canvas.direction == (-1, 0)

    # Now turning Up via 'W' key is a 90-degree turn
    event_w = QKeyEvent(QEvent.KeyPress, Qt.Key_W, Qt.NoModifier)
    canvas.keyPressEvent(event_w)
    assert canvas.next_direction == (0, -1)

    # Tick advances direction to Up (0, -1)
    canvas._tick()
    assert canvas.direction == (0, -1)

    # Prevent instant 180-degree reversal: Down (S) while moving Up
    event_s = QKeyEvent(QEvent.KeyPress, Qt.Key_S, Qt.NoModifier)
    canvas.keyPressEvent(event_s)
    # next_direction should NOT change to (0, 1)
    assert canvas.next_direction == (0, -1)


def test_snake_eating_food(qapp):
    canvas = SnakeCanvas()
    canvas.start_game()

    canvas.snake = [(5, 5), (4, 5), (3, 5)]
    canvas.direction = (1, 0)
    canvas.next_direction = (1, 0)
    canvas.food = (6, 5)

    canvas._tick()

    assert canvas.snake[0] == (6, 5)
    assert len(canvas.snake) == 4
    assert canvas.score == 10
    assert canvas.high_score == 10
    # New food was spawned and is not inside snake
    assert canvas.food not in canvas.snake


def test_snake_wall_collision(qapp):
    canvas = SnakeCanvas()
    canvas.start_game()

    # Place head at right edge moving right
    canvas.snake = [(GRID_COLS - 1, 5), (GRID_COLS - 2, 5), (GRID_COLS - 3, 5)]
    canvas.direction = (1, 0)
    canvas.next_direction = (1, 0)

    canvas._tick()

    assert canvas.state == STATE_GAME_OVER
    assert not canvas._timer.isActive()


def test_snake_self_collision(qapp):
    canvas = SnakeCanvas()
    canvas.start_game()

    # Form a loop
    canvas.snake = [(5, 5), (5, 6), (4, 6), (4, 5), (4, 4)]
    canvas.direction = (-1, 0)
    canvas.next_direction = (-1, 0)  # Next head (4, 5) is in snake body

    canvas._tick()

    assert canvas.state == STATE_GAME_OVER
    assert not canvas._timer.isActive()


def test_snake_restart_from_game_over(qapp):
    canvas = SnakeCanvas()
    canvas.start_game()
    canvas._game_over()
    assert canvas.state == STATE_GAME_OVER

    # Press 'R'
    event_r = QKeyEvent(QEvent.KeyPress, Qt.Key_R, Qt.NoModifier)
    canvas.keyPressEvent(event_r)

    assert canvas.state == STATE_PLAYING
    assert canvas._timer.isActive()
    assert canvas.score == 0


def test_statusbar_snake_ai_independence(qapp):
    bus = EventBus()
    status_bar = AtlasStatusBar(bus=bus)

    assert hasattr(status_bar, "snake_card")
    card = status_bar.snake_card
    canvas = card.canvas

    canvas.start_game()
    assert canvas.state == STATE_PLAYING
    assert canvas._timer.isActive()

    # Emit all kinds of AI lifecycle events through the bus
    bus.publish(ThinkingStarted())
    bus.publish(ChunkReceived("first chunk"))
    bus.publish(ChunkReceived("second chunk"))
    bus.publish(ThinkingFinished())
    bus.publish(ErrorOccurred("something went wrong"))

    # Status bar periodic refresh
    status_bar.refresh()

    # Verify snake state remained unaffected
    assert canvas.state == STATE_PLAYING
    assert canvas._timer.isActive()

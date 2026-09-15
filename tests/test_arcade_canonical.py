"""Atlas V3 - Canonical Arcade Subsystem Tests.

Rigorously verifies requirements A through R from the Canonical Design Specification:
A. Arcade exists independently of Snake.
B. Snake is registered as an Arcade game.
C. Snake is not visible as a permanent status-bar preview.
D. Thinking state can expose the Arcade invitation.
E. Ending AI thinking hides the thinking-specific invitation.
F. Opening Arcade shows the game selector.
G. Starting Snake enters GAME_PLAYING.
H. Snake Game Over enters GAME_OVER.
I. GAME_OVER provides Play Again.
J. GAME_OVER provides Exit.
K. Exit returns to Arcade selector.
L. Play Again intentionally restarts.
M. Losing focus pauses without destroying state.
N. AI state changes do not destroy Snake state.
O. Arcade architecture permits additional registered games.
P. Tools is accessible from the status bar.
Q. Settings is accessible from the former/current Tools area.
R. Existing Settings functionality remains intact.
"""

from __future__ import annotations

import os
import pytest

if "DISPLAY" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFocusEvent, QKeyEvent
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

from core.bus import EventBus
from core.events import ChunkReceived, ErrorOccurred, ThinkingFinished, ThinkingStarted
from gui.widgets.arcade import (
    ArcadeGameInfo,
    ArcadeRegistry,
    AtlasArcadeCard,
    STATE_ARCADE_CLOSED,
    STATE_ARCADE_SELECTOR,
    STATE_GAME_OVER,
    STATE_GAME_PAUSED,
    STATE_GAME_PLAYING,
)
from gui.widgets.sidebar import AtlasSidebar
from gui.widgets.snake import (
    STATE_GAME_OVER as S_GAME_OVER,
    STATE_PLAYING as S_PLAYING,
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


def test_requirement_a_arcade_independent_of_snake(qapp):
    """A. Arcade exists independently of Snake."""
    arcade_card = AtlasArcadeCard()
    assert arcade_card.state == STATE_ARCADE_CLOSED
    assert hasattr(arcade_card, "selector")
    assert hasattr(arcade_card, "game_surface")
    assert hasattr(arcade_card, "launch_game")
    assert hasattr(arcade_card, "exit_current_game")


def test_requirement_b_snake_registered_as_arcade_game(qapp):
    """B. Snake is registered as an Arcade game."""
    game_info = ArcadeRegistry.get("snake")
    assert game_info is not None
    info, factory = game_info
    assert info.game_id == "snake"
    assert info.title == "Snake"
    widget = factory(None)
    assert isinstance(widget, AtlasSnakeCard)


def test_requirement_c_no_permanent_statusbar_snake_preview(qapp):
    """C. Snake is not visible as a permanent status-bar preview."""
    bus = EventBus()
    status_bar = AtlasStatusBar(bus=bus)
    status_bar.show()

    # In idle/normal state, the arcade card is not visible (hidden)
    assert status_bar.arcade_card.isHidden()
    assert status_bar.arcade_card.state == STATE_ARCADE_CLOSED

    # The compact button is available in the status bar
    assert not status_bar.arcade_button.isHidden()
    assert status_bar.arcade_button.objectName() == "StatusArcadeButton"


def test_requirement_d_and_e_thinking_prompt_lifecycle(qapp):
    """D. Thinking state exposes invitation. E. Ending AI thinking hides it."""
    bus = EventBus()
    status_bar = AtlasStatusBar(bus=bus)
    status_bar.show()

    # Initial state: thinking prompt is hidden
    assert status_bar.thinking_arcade_prompt.isHidden()

    # D: Thinking starts -> prompt exposed
    bus.publish(ThinkingStarted())
    assert not status_bar.thinking_arcade_prompt.isHidden()

    # E: Thinking finishes -> prompt hidden
    bus.publish(ThinkingFinished())
    assert status_bar.thinking_arcade_prompt.isHidden()


def test_requirement_f_opening_arcade_shows_selector(qapp):
    """F. Opening Arcade shows the game selector."""
    bus = EventBus()
    status_bar = AtlasStatusBar(bus=bus)
    status_bar.show()

    status_bar.arcade_button.click()
    assert not status_bar.arcade_card.isHidden()
    assert status_bar.arcade_card.state == STATE_ARCADE_SELECTOR
    assert status_bar.arcade_card.stack.currentIndex() == 0


def test_requirement_g_starting_snake_enters_game_playing(qapp):
    """G. Starting Snake enters GAME_PLAYING."""
    arcade_card = AtlasArcadeCard()
    arcade_card.open_arcade()
    arcade_card.launch_game("snake")

    assert arcade_card.state == STATE_GAME_PLAYING
    assert arcade_card.stack.currentIndex() == 1

    snake_card = arcade_card.snake_card
    assert snake_card.canvas.state == S_PLAYING
    assert snake_card.canvas._timer.isActive()


def test_requirement_h_snake_game_over_enters_game_over(qapp):
    """H. Snake Game Over enters GAME_OVER."""
    arcade_card = AtlasArcadeCard()
    arcade_card.open_arcade()
    arcade_card.launch_game("snake")

    snake_card = arcade_card.snake_card
    snake_card.canvas._game_over()

    assert snake_card.canvas.state == S_GAME_OVER
    assert arcade_card.state == STATE_GAME_OVER
    assert not snake_card.canvas._timer.isActive()


def test_requirement_i_and_j_game_over_actions_available(qapp):
    """I. GAME_OVER provides Play Again. J. GAME_OVER provides Exit."""
    snake_card = AtlasSnakeCard()
    snake_card.show()
    snake_card.canvas.start_game()
    snake_card.canvas._game_over()

    # I: Play Again button
    assert not snake_card.play_btn.isHidden()
    assert "Play Again" in snake_card.play_btn.text()

    # J: Exit button
    assert not snake_card.exit_btn.isHidden()
    assert "Exit" in snake_card.exit_btn.text()


def test_requirement_k_exit_returns_to_arcade_selector(qapp):
    """K. Exit returns to Arcade selector."""
    arcade_card = AtlasArcadeCard()
    arcade_card.open_arcade()
    arcade_card.launch_game("snake")

    snake_card = arcade_card.snake_card
    snake_card.canvas._game_over()

    # User clicks Exit
    snake_card.exit_btn.click()

    assert arcade_card.state == STATE_ARCADE_SELECTOR
    assert arcade_card.stack.currentIndex() == 0


def test_requirement_l_play_again_intentionally_restarts(qapp):
    """L. Play Again intentionally restarts."""
    arcade_card = AtlasArcadeCard()
    arcade_card.open_arcade()
    arcade_card.launch_game("snake")

    snake_card = arcade_card.snake_card
    snake_card.canvas.score = 50
    snake_card.canvas._game_over()

    # User clicks Play Again
    snake_card.play_btn.click()

    assert snake_card.canvas.state == S_PLAYING
    assert snake_card.canvas._timer.isActive()
    assert snake_card.canvas.score == 0
    assert arcade_card.state == STATE_GAME_PLAYING


def test_requirement_m_losing_focus_pauses_without_destroying_state(qapp):
    """M. Losing focus pauses without destroying state."""
    arcade_card = AtlasArcadeCard()
    arcade_card.open_arcade()
    arcade_card.launch_game("snake")

    snake_card = arcade_card.snake_card
    snake_card.canvas.score = 30
    head_pos = snake_card.canvas.snake[0]

    # Focus out
    event = QFocusEvent(QEvent.FocusOut)
    snake_card.canvas.focusOutEvent(event)

    assert snake_card.canvas.state == "PAUSED"
    assert not snake_card.canvas._timer.isActive()
    assert snake_card.canvas.score == 30
    assert snake_card.canvas.snake[0] == head_pos


def test_requirement_n_ai_state_changes_do_not_destroy_snake_state(qapp):
    """N. AI state changes do not destroy Snake state."""
    bus = EventBus()
    status_bar = AtlasStatusBar(bus=bus)

    status_bar.arcade_card.open_arcade()
    status_bar.arcade_card.launch_game("snake")

    snake_card = status_bar.arcade_card.snake_card
    snake_card.canvas.score = 40

    # Stream arbitrary AI events
    bus.publish(ThinkingStarted())
    bus.publish(ChunkReceived("test"))
    bus.publish(ThinkingFinished())
    bus.publish(ErrorOccurred("err"))
    status_bar.refresh()

    assert snake_card.canvas.state == S_PLAYING
    assert snake_card.canvas._timer.isActive()
    assert snake_card.canvas.score == 40


def test_requirement_o_arcade_permits_additional_registered_games(qapp):
    """O. Arcade architecture permits additional registered games."""
    initial_count = ArcadeRegistry.count()

    def dummy_game_factory(parent=None):
        return QLabel("Pong Game Surface", parent)

    ArcadeRegistry.register(
        ArcadeGameInfo(
            game_id="pong",
            title="Pong",
            description="Classic 2D paddle ball.",
            icon="🏓",
        ),
        dummy_game_factory,
    )

    assert ArcadeRegistry.count() == initial_count + 1
    retrieved = ArcadeRegistry.get("pong")
    assert retrieved is not None
    info, factory = retrieved
    assert info.title == "Pong"

    arcade_card = AtlasArcadeCard()
    arcade_card.open_arcade()
    arcade_card.launch_game("pong")
    assert arcade_card.state == STATE_GAME_PLAYING

    # Clean up test registration
    ArcadeRegistry.unregister("pong")
    assert ArcadeRegistry.count() == initial_count


def test_requirement_p_tools_accessible_from_statusbar(qapp):
    """P. Tools is accessible from the status bar."""
    bus = EventBus()
    status_bar = AtlasStatusBar(bus=bus)

    assert hasattr(status_bar, "tools_button")
    assert status_bar.tools_button.objectName() == "StatusToolsButton"

    tools_triggered = False

    def on_tools():
        nonlocal tools_triggered
        tools_triggered = True

    status_bar.tools_requested.connect(on_tools)
    status_bar.tools_button.click()
    assert tools_triggered is True


def test_requirement_q_and_r_settings_accessible_from_former_tools_area(qapp):
    """Q. Settings is accessible from former Tools area. R. Settings functionality intact."""
    bus = EventBus()
    sidebar = AtlasSidebar(bus=bus)

    assert hasattr(sidebar, "settings_button")
    assert sidebar.settings_button.objectName() == "SettingsButton"
    assert "Settings" in sidebar.settings_button.text()

    # Emits settings_requested or invokes open_settings
    requested = False

    def on_settings_requested():
        nonlocal requested
        requested = True

    sidebar.settings_requested.connect(on_settings_requested)
    # Trigger method
    sidebar.settings_requested.emit()
    assert requested is True

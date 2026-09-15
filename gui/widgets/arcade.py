"""Atlas V3 Arcade Subsystem.

A future-proof native Qt Arcade framework that hosts lightweight mini-games
independently of Atlas AI runtime state. Conforms to docs/design/ATLAS_DESIGN_SYSTEM_V1.md.

Architecture:
Arcade
 ├── Game Registry (ArcadeRegistry)
 │    ├── Snake (and future games)
 ├── Arcade Launcher / Selector (ArcadeSelectorWidget)
 └── Game Surface (ArcadeGameSurface / AtlasArcadeCard)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

# Explicit Arcade lifecycle states
STATE_ARCADE_CLOSED = "ARCADE_CLOSED"
STATE_ARCADE_SELECTOR = "ARCADE_SELECTOR"
STATE_GAME_PLAYING = "GAME_PLAYING"
STATE_GAME_PAUSED = "GAME_PAUSED"
STATE_GAME_OVER = "GAME_OVER"


@dataclass
class ArcadeGameInfo:
    """Metadata describing a registered arcade game."""

    game_id: str
    title: str
    description: str
    icon: str = "🎮"
    author: str = "Atlas"


class ArcadeRegistry:
    """Future-proof registry of playable native Qt games in Atlas Arcade."""

    _registry: Dict[str, Tuple[ArcadeGameInfo, Callable[[Optional[QWidget]], QWidget]]] = {}

    @classmethod
    def register(
        cls,
        info: ArcadeGameInfo,
        factory: Callable[[Optional[QWidget]], QWidget],
    ):
        cls._registry[info.game_id] = (info, factory)

    @classmethod
    def unregister(cls, game_id: str):
        cls._registry.pop(game_id, None)

    @classmethod
    def get(
        cls, game_id: str
    ) -> Optional[Tuple[ArcadeGameInfo, Callable[[Optional[QWidget]], QWidget]]]:
        return cls._registry.get(game_id)

    @classmethod
    def list_games(cls) -> List[ArcadeGameInfo]:
        return [info for info, _ in cls._registry.values()]

    @classmethod
    def count(cls) -> int:
        return len(cls._registry)

    @classmethod
    def clear(cls):
        cls._registry.clear()


class ArcadeGameCard(QFrame):
    """Entry card in the Arcade Selector for a single registered game."""

    play_requested = Signal(str)  # game_id

    def __init__(self, info: ArcadeGameInfo, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.info = info
        self.setObjectName("ArcadeGameItem")
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(
            """
            QFrame#ArcadeGameItem {
                background-color: #18181C;
                border: 1px solid #27272F;
                border-radius: 6px;
                padding: 6px;
            }
            QFrame#ArcadeGameItem:hover {
                border-color: #398C8F;
                background-color: #1C1C22;
            }
            """
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Icon
        icon_label = QLabel(self.info.icon)
        icon_label.setStyleSheet("font-size: 14pt;")
        layout.addWidget(icon_label)

        # Meta (Title + Description)
        meta_layout = QVBoxLayout()
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_layout.setSpacing(1)

        title_label = QLabel(self.info.title)
        title_label.setStyleSheet("color: #F4F4F5; font-weight: 600; font-size: 8.5pt;")
        meta_layout.addWidget(title_label)

        desc_label = QLabel(self.info.description)
        desc_label.setStyleSheet("color: #A1A1AA; font-size: 7.5pt;")
        desc_label.setWordWrap(True)
        meta_layout.addWidget(desc_label)

        layout.addLayout(meta_layout, 1)

        # Play button
        self.play_button = QPushButton("▶ Play")
        self.play_button.setObjectName(f"PlayButton_{self.info.game_id}")
        self.play_button.setCursor(Qt.PointingHandCursor)
        self.play_button.setFixedHeight(24)
        self.play_button.setStyleSheet(
            """
            QPushButton {
                background-color: #1F2937;
                color: #4FB8BA;
                border: 1px solid #398C8F;
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 8pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #398C8F;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #2A7376;
            }
            """
        )
        self.play_button.clicked.connect(lambda: self.play_requested.emit(self.info.game_id))
        layout.addWidget(self.play_button)


class ArcadeSelectorWidget(QFrame):
    """Launcher and game selector interface for Atlas Arcade."""

    game_selected = Signal(str)  # game_id
    close_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("ArcadeSelector")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)

        # Header bar
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(4)

        title = QLabel("ATLAS ARCADE")
        title.setObjectName("StatusCardTitle")
        title.setStyleSheet("color: #71717A; font-size: 8pt; font-weight: 700; letter-spacing: 0.5px;")
        header.addWidget(title)

        header.addStretch(1)

        self.close_button = QPushButton("✕")
        self.close_button.setObjectName("ArcadeCloseButton")
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setFixedSize(18, 18)
        self.close_button.setToolTip("Close Arcade")
        self.close_button.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: #82828C;
                border: none;
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #F87171;
            }
            """
        )
        self.close_button.clicked.connect(self.close_requested.emit)
        header.addWidget(self.close_button)

        layout.addLayout(header)

        # Games container
        self.games_container = QVBoxLayout()
        self.games_container.setContentsMargins(0, 0, 0, 0)
        self.games_container.setSpacing(6)
        layout.addLayout(self.games_container)

        self.refresh_games()

    def refresh_games(self):
        # Clear existing
        while self.games_container.count():
            item = self.games_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        games = ArcadeRegistry.list_games()
        if not games:
            empty_lbl = QLabel("No games installed")
            empty_lbl.setStyleSheet("color: #71717A; font-size: 8pt; font-style: italic;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.games_container.addWidget(empty_lbl)
            return

        for info in games:
            card = ArcadeGameCard(info, self)
            card.play_requested.connect(self.game_selected.emit)
            self.games_container.addWidget(card)


class AtlasArcadeCard(QFrame):
    """Main Arcade container embedding selector and active game surfaces into AtlasStatusBar."""

    state_changed = Signal(str)
    arcade_opened = Signal()
    arcade_closed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("ArcadeCard")
        self.state: str = STATE_ARCADE_CLOSED
        self._active_game_id: Optional[str] = None
        self._game_instances: Dict[str, QWidget] = {}

        self._build_ui()
        self.hide()

    def _build_ui(self):
        self.setStyleSheet(
            """
            QFrame#ArcadeCard {
                background-color: #141418;
                border: 1px solid #27272F;
                border-radius: 6px;
                padding: 6px;
            }
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.stack = QStackedWidget(self)

        # Page 0: Arcade Selector
        self.selector = ArcadeSelectorWidget(self)
        self.selector.close_requested.connect(self.close_arcade)
        self.selector.game_selected.connect(self.launch_game)
        self.stack.addWidget(self.selector)

        # Page 1: Game Surface Container
        self.game_surface = QWidget(self)
        self.surface_layout = QVBoxLayout(self.game_surface)
        self.surface_layout.setContentsMargins(0, 0, 0, 0)
        self.surface_layout.setSpacing(0)
        self.stack.addWidget(self.game_surface)

        layout.addWidget(self.stack)

    # ------------------------------------------------------------------
    # Game Instance Management
    # ------------------------------------------------------------------

    def _get_or_create_game(self, game_id: str) -> Optional[QWidget]:
        if game_id in self._game_instances:
            return self._game_instances[game_id]

        entry = ArcadeRegistry.get(game_id)
        if entry is None:
            return None

        _, factory = entry
        game_widget = factory(self.game_surface)

        # If game widget has exit_requested signal, connect it
        if hasattr(game_widget, "exit_requested"):
            game_widget.exit_requested.connect(self.exit_current_game)

        # If game widget has state_changed signal, synchronize
        if hasattr(game_widget, "state_changed"):
            game_widget.state_changed.connect(self._on_subgame_state_changed)

        self._game_instances[game_id] = game_widget
        return game_widget

    def _on_subgame_state_changed(self, sub_state: str):
        from gui.widgets.snake import (
            STATE_GAME_OVER as S_GAME_OVER,
            STATE_PAUSED as S_PAUSED,
            STATE_PLAYING as S_PLAYING,
        )

        if sub_state == S_PLAYING:
            self.state = STATE_GAME_PLAYING
        elif sub_state == S_PAUSED:
            self.state = STATE_GAME_PAUSED
        elif sub_state == S_GAME_OVER:
            self.state = STATE_GAME_OVER

        self.state_changed.emit(self.state)

    # ------------------------------------------------------------------
    # Lifecycle & Controls
    # ------------------------------------------------------------------

    def open_arcade(self):
        """Open the Arcade. If a game is active, resumes view; else shows selector."""
        self.show()
        if self._active_game_id and self._active_game_id in self._game_instances:
            self.stack.setCurrentIndex(1)
            game_widget = self._game_instances[self._active_game_id]
            if hasattr(game_widget, "canvas"):
                self._on_subgame_state_changed(game_widget.canvas.state)
            else:
                self.state = STATE_GAME_PLAYING
                self.state_changed.emit(self.state)
        else:
            self.selector.refresh_games()
            self.stack.setCurrentIndex(0)
            self.state = STATE_ARCADE_SELECTOR
            self.state_changed.emit(self.state)

        self.arcade_opened.emit()

    def close_arcade(self):
        """Close the Arcade panel and pause any active game without destroying state."""
        if self._active_game_id and self._active_game_id in self._game_instances:
            game_widget = self._game_instances[self._active_game_id]
            if hasattr(game_widget, "canvas") and hasattr(game_widget.canvas, "pause_game"):
                game_widget.canvas.pause_game()

        self.state = STATE_ARCADE_CLOSED
        self.hide()
        self.state_changed.emit(self.state)
        self.arcade_closed.emit()

    def launch_game(self, game_id: str):
        """Launch a registered game into the game surface."""
        game_widget = self._get_or_create_game(game_id)
        if game_widget is None:
            return

        # Clear active surface layout
        while self.surface_layout.count():
            item = self.surface_layout.takeAt(0)
            w = item.widget()
            if w and w != game_widget:
                w.setParent(None)

        self.surface_layout.addWidget(game_widget)
        self._active_game_id = game_id

        # Show game page
        self.stack.setCurrentIndex(1)

        # Start game if applicable
        if hasattr(game_widget, "canvas") and hasattr(game_widget.canvas, "start_game"):
            game_widget.canvas.start_game()
            self.state = STATE_GAME_PLAYING
        else:
            self.state = STATE_GAME_PLAYING

        self.show()
        self.state_changed.emit(self.state)

    def exit_current_game(self):
        """Exit the current game session and return to the Arcade selector."""
        if self._active_game_id and self._active_game_id in self._game_instances:
            game_widget = self._game_instances[self._active_game_id]
            if hasattr(game_widget, "canvas") and hasattr(game_widget.canvas, "pause_game"):
                game_widget.canvas.pause_game()

        self.selector.refresh_games()
        self.stack.setCurrentIndex(0)
        self.state = STATE_ARCADE_SELECTOR
        self.state_changed.emit(self.state)

    @property
    def snake_card(self):
        """Backward-compatible access to the Snake game card."""
        return self._get_or_create_game("snake")

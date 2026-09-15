"""Atlas V3 Embedded Snake Game for Atlas Arcade.

A self-contained native Qt Snake game registered as a mini-game within the
Atlas Arcade system. Conforms to docs/design/ATLAS_DESIGN_SYSTEM_V1.md.
"""

from __future__ import annotations

import random
from typing import List, Optional, Tuple

from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QKeyEvent, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Game states
STATE_IDLE = "IDLE"
STATE_PLAYING = "PLAYING"
STATE_PAUSED = "PAUSED"
STATE_GAME_OVER = "GAME_OVER"

# Grid configuration
GRID_COLS = 16
GRID_ROWS = 11
CELL_SIZE = 14  # 16 * 14 = 224px width, 11 * 14 = 154px height


class SnakeCanvas(QWidget):
    """Native QPainter canvas implementing Snake game logic and state machine."""

    score_changed = Signal(int, int)  # current, high_score
    state_changed = Signal(str)  # new state string
    exit_requested = Signal()  # user requests returning to arcade selector

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setFixedSize(GRID_COLS * CELL_SIZE, GRID_ROWS * CELL_SIZE)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_Hover, True)

        self.state: str = STATE_IDLE
        self.score: int = 0
        self.high_score: int = 0

        # Snake representation: list of (x, y) coordinates, head is at index 0
        self.snake: List[Tuple[int, int]] = []
        self.direction: Tuple[int, int] = (1, 0)
        self.next_direction: Tuple[int, int] = (1, 0)
        self.food: Tuple[int, int] = (10, 5)

        self._timer = QTimer(self)
        self._timer.setInterval(125)  # ~8 steps per second
        self._timer.timeout.connect(self._tick)

        self._reset_snake()

    def _reset_snake(self):
        mid_y = GRID_ROWS // 2
        self.snake = [(5, mid_y), (4, mid_y), (3, mid_y)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self._spawn_food()

    def _spawn_food(self):
        empty_cells = [
            (x, y)
            for x in range(GRID_COLS)
            for y in range(GRID_ROWS)
            if (x, y) not in self.snake
        ]
        if empty_cells:
            self.food = random.choice(empty_cells)
        else:
            self.food = (-1, -1)

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def start_game(self):
        """Start a new game session."""
        self._reset_snake()
        self.score = 0
        self.score_changed.emit(self.score, self.high_score)
        self.state = STATE_PLAYING
        self.state_changed.emit(self.state)
        self._timer.start()
        self.update()

    def pause_game(self):
        """Pause the current game session, preserving snake, food, and score."""
        if self.state == STATE_PLAYING:
            self.state = STATE_PAUSED
            self._timer.stop()
            self.state_changed.emit(self.state)
            self.update()

    def resume_game(self):
        """Resume the paused game session."""
        if self.state == STATE_PAUSED:
            self.state = STATE_PLAYING
            self.state_changed.emit(self.state)
            self._timer.start()
            self.update()

    def toggle_pause(self):
        """Toggle pause/resume, or start game if idle or game over."""
        if self.state == STATE_PLAYING:
            self.pause_game()
        elif self.state == STATE_PAUSED:
            self.resume_game()
        elif self.state in (STATE_IDLE, STATE_GAME_OVER):
            self.start_game()

    def restart_game(self):
        """Restart game regardless of current state."""
        self.start_game()

    def _game_over(self):
        self._timer.stop()
        self.state = STATE_GAME_OVER
        if self.score > self.high_score:
            self.high_score = self.score
        self.score_changed.emit(self.score, self.high_score)
        self.state_changed.emit(self.state)
        self.update()

    # ------------------------------------------------------------------
    # Game tick
    # ------------------------------------------------------------------

    def _tick(self):
        if self.state != STATE_PLAYING:
            return

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        next_head = (head_x + dx, head_y + dy)

        # Wall collision
        if not (0 <= next_head[0] < GRID_COLS and 0 <= next_head[1] < GRID_ROWS):
            self._game_over()
            return

        # Self collision (ignoring tail tip since it will advance)
        if next_head in self.snake[:-1]:
            self._game_over()
            return

        # Advance snake
        self.snake.insert(0, next_head)

        # Food collision
        if next_head == self.food:
            self.score += 10
            if self.score > self.high_score:
                self.high_score = self.score
            self.score_changed.emit(self.score, self.high_score)
            self._spawn_food()
        else:
            self.snake.pop()

        self.update()

    # ------------------------------------------------------------------
    # Input Handling
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        # Direction mappings (Arrows & WASD)
        dir_map = {
            Qt.Key_Up: (0, -1),
            Qt.Key_W: (0, -1),
            Qt.Key_Down: (0, 1),
            Qt.Key_S: (0, 1),
            Qt.Key_Left: (-1, 0),
            Qt.Key_A: (-1, 0),
            Qt.Key_Right: (1, 0),
            Qt.Key_D: (1, 0),
        }

        if key in dir_map:
            new_dir = dir_map[key]

            if self.state == STATE_IDLE:
                self.next_direction = new_dir
                self.start_game()
                event.accept()
                return

            if self.state == STATE_PAUSED:
                self.resume_game()
                if (new_dir[0] != -self.direction[0] or new_dir[0] == 0) and (
                    new_dir[1] != -self.direction[1] or new_dir[1] == 0
                ):
                    self.next_direction = new_dir
                event.accept()
                return

            if self.state == STATE_GAME_OVER:
                self.start_game()
                event.accept()
                return

            if self.state == STATE_PLAYING:
                # Prevent 180-degree instant suicide
                if (new_dir[0] != -self.direction[0] or new_dir[0] == 0) and (
                    new_dir[1] != -self.direction[1] or new_dir[1] == 0
                ):
                    self.next_direction = new_dir
                event.accept()
                return

        if key == Qt.Key_Space:
            self.toggle_pause()
            event.accept()
            return

        if key == Qt.Key_R:
            self.restart_game()
            event.accept()
            return

        if key == Qt.Key_Escape:
            self.exit_requested.emit()
            event.accept()
            return

        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        self.setFocus()
        if self.state in (STATE_IDLE, STATE_GAME_OVER):
            self.start_game()
        elif self.state == STATE_PAUSED:
            self.resume_game()
        elif self.state == STATE_PLAYING:
            self.pause_game()
        event.accept()

    def focusOutEvent(self, event):
        # Auto-pause when user navigates away or unfocuses
        if self.state == STATE_PLAYING:
            self.pause_game()
        super().focusOutEvent(event)
        self.update()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.update()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        width = GRID_COLS * CELL_SIZE
        height = GRID_ROWS * CELL_SIZE

        # 1. Background
        bg_color = QColor("#141418")
        painter.fillRect(0, 0, width, height, bg_color)

        # 2. Subtle grid lines / dots
        grid_pen = QPen(QColor("#1F1F26"))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for x in range(1, GRID_COLS):
            painter.drawLine(x * CELL_SIZE, 0, x * CELL_SIZE, height)
        for y in range(1, GRID_ROWS):
            painter.drawLine(0, y * CELL_SIZE, width, y * CELL_SIZE)

        # 3. Outer border (highlighted if focused)
        painter.setRenderHint(QPainter.Antialiasing, True)
        if self.hasFocus():
            border_pen = QPen(QColor("#398C8F"), 1.5)
        else:
            border_pen = QPen(QColor("#27272F"), 1.0)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(0, 0, width - 1, height - 1, 4, 4)

        # 4. Food
        fx, fy = self.food
        if 0 <= fx < GRID_COLS and 0 <= fy < GRID_ROWS:
            food_rect = QRect(
                fx * CELL_SIZE + 2,
                fy * CELL_SIZE + 2,
                CELL_SIZE - 4,
                CELL_SIZE - 4,
            )
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#4ADE80"))  # Semantic Success Green
            painter.drawRoundedRect(food_rect, 3, 3)

        # 5. Snake Body and Head
        for i, (sx, sy) in enumerate(self.snake):
            seg_rect = QRect(
                sx * CELL_SIZE + 1,
                sy * CELL_SIZE + 1,
                CELL_SIZE - 2,
                CELL_SIZE - 2,
            )
            if i == 0:
                # Head
                painter.setPen(QColor("#2A7376"))
                painter.setBrush(QColor("#4FB8BA"))  # Brand text cyan
                painter.drawRoundedRect(seg_rect, 3, 3)

                # Eye indicators
                painter.setBrush(QColor("#09090B"))
                painter.setPen(Qt.NoPen)
                eye_r = 1.5
                dx, dy = self.direction
                cx = seg_rect.center().x()
                cy = seg_rect.center().y()
                if dx == 1:  # right
                    painter.drawEllipse(QPoint(cx + 2, cy - 2), eye_r, eye_r)
                    painter.drawEllipse(QPoint(cx + 2, cy + 2), eye_r, eye_r)
                elif dx == -1:  # left
                    painter.drawEllipse(QPoint(cx - 2, cy - 2), eye_r, eye_r)
                    painter.drawEllipse(QPoint(cx - 2, cy + 2), eye_r, eye_r)
                elif dy == -1:  # up
                    painter.drawEllipse(QPoint(cx - 2, cy - 2), eye_r, eye_r)
                    painter.drawEllipse(QPoint(cx + 2, cy - 2), eye_r, eye_r)
                else:  # down
                    painter.drawEllipse(QPoint(cx - 2, cy + 2), eye_r, eye_r)
                    painter.drawEllipse(QPoint(cx + 2, cy + 2), eye_r, eye_r)
            else:
                # Body
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor("#398C8F"))  # Brand UI
                painter.drawRoundedRect(seg_rect, 2, 2)

        # 6. Overlays for IDLE, PAUSED, GAME_OVER
        if self.state in (STATE_IDLE, STATE_PAUSED, STATE_GAME_OVER):
            overlay = QColor(9, 9, 11, 215)  # 85% opacity BG_BASE
            painter.fillRect(0, 0, width, height, overlay)

            font = QFont("Inter", 9)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor("#F4F4F5"))

            if self.state == STATE_IDLE:
                painter.drawText(
                    QRect(0, 30, width, 24),
                    Qt.AlignCenter,
                    "ARCADE SNAKE",
                )
                font_sub = QFont("Inter", 8)
                font_sub.setBold(False)
                painter.setFont(font_sub)
                painter.setPen(QColor("#A1A1AA"))
                painter.drawText(
                    QRect(0, 56, width, 20),
                    Qt.AlignCenter,
                    "Click or Press Space to Play",
                )
                painter.drawText(
                    QRect(0, 76, width, 20),
                    Qt.AlignCenter,
                    "Arrows / WASD to move",
                )

            elif self.state == STATE_PAUSED:
                painter.drawText(
                    QRect(0, 42, width, 24),
                    Qt.AlignCenter,
                    "PAUSED",
                )
                font_sub = QFont("Inter", 8)
                font_sub.setBold(False)
                painter.setFont(font_sub)
                painter.setPen(QColor("#A1A1AA"))
                painter.drawText(
                    QRect(0, 68, width, 20),
                    Qt.AlignCenter,
                    "Press Space or Click to Resume",
                )

            elif self.state == STATE_GAME_OVER:
                painter.setPen(QColor("#F87171"))  # Error red
                painter.drawText(
                    QRect(0, 24, width, 24),
                    Qt.AlignCenter,
                    "GAME OVER",
                )
                font_sub = QFont("Inter", 8)
                font_sub.setBold(False)
                painter.setFont(font_sub)
                painter.setPen(QColor("#F4F4F5"))
                painter.drawText(
                    QRect(0, 48, width, 20),
                    Qt.AlignCenter,
                    f"Score: {self.score}   Best: {self.high_score}",
                )
                painter.setPen(QColor("#A1A1AA"))
                painter.drawText(
                    QRect(0, 72, width, 20),
                    Qt.AlignCenter,
                    "Play Again  •  Exit to Arcade",
                )
                painter.drawText(
                    QRect(0, 92, width, 20),
                    Qt.AlignCenter,
                    "[Space/R] Restart   [Esc] Exit",
                )


class AtlasSnakeCard(QFrame):
    """Container card embedding Snake canvas into Arcade/Status Bar."""

    state_changed = Signal(str)
    exit_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setObjectName("StatusCard")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(6)

        # Header bar with Back-to-Arcade, Title, and Score
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        self.back_button = QPushButton("← Arcade")
        self.back_button.setObjectName("SnakeBackButton")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.setFixedHeight(20)
        self.back_button.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: #82828C;
                border: 1px solid #27272F;
                border-radius: 3px;
                padding: 1px 6px;
                font-size: 7.5pt;
                font-weight: 500;
            }
            QPushButton:hover {
                color: #F4F4F5;
                background-color: #1C1C22;
                border-color: #398C8F;
            }
            """
        )
        self.back_button.clicked.connect(self._on_exit_clicked)
        header_layout.addWidget(self.back_button)

        self.title_label = QLabel("SNAKE")
        self.title_label.setObjectName("StatusCardTitle")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch(1)

        self.score_label = QLabel("0 | Best: 0")
        self.score_label.setStyleSheet("color: #4FB8BA; font-size: 8.5pt; font-weight: 600;")
        header_layout.addWidget(self.score_label)

        layout.addLayout(header_layout)

        # Center canvas
        canvas_container = QHBoxLayout()
        canvas_container.setContentsMargins(0, 0, 0, 0)
        canvas_container.setAlignment(Qt.AlignCenter)

        self.canvas = SnakeCanvas(self)
        self.canvas.score_changed.connect(self._on_score_changed)
        self.canvas.state_changed.connect(self._on_state_changed)
        self.canvas.exit_requested.connect(self._on_exit_clicked)
        canvas_container.addWidget(self.canvas)

        layout.addLayout(canvas_container)

        # Bottom controls bar
        self.controls_layout = QHBoxLayout()
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_layout.setSpacing(6)

        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setObjectName("SnakePlayButton")
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setFixedHeight(22)
        self.play_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #1C1C22;
                color: #A1A1AA;
                border: 1px solid #27272F;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 8pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #27272F;
                color: #F4F4F5;
                border-color: #398C8F;
            }
            QPushButton:pressed {
                background-color: #121215;
                color: #4FB8BA;
            }
            """
        )
        self.play_btn.clicked.connect(self._toggle_play)
        self.controls_layout.addWidget(self.play_btn)

        self.restart_btn = QPushButton("↺ Restart")
        self.restart_btn.setObjectName("SnakeRestartButton")
        self.restart_btn.setCursor(Qt.PointingHandCursor)
        self.restart_btn.setFixedHeight(22)
        self.restart_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #1C1C22;
                color: #82828C;
                border: 1px solid #27272F;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 8pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #27272F;
                color: #F4F4F5;
                border-color: #3F3F4A;
            }
            QPushButton:pressed {
                background-color: #121215;
                color: #F87171;
            }
            """
        )
        self.restart_btn.clicked.connect(self.canvas.restart_game)
        self.controls_layout.addWidget(self.restart_btn)

        self.exit_btn = QPushButton("← Exit")
        self.exit_btn.setObjectName("SnakeExitButton")
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        self.exit_btn.setFixedHeight(22)
        self.exit_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #1C1C22;
                color: #82828C;
                border: 1px solid #27272F;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 8pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #27272F;
                color: #F87171;
                border-color: #F87171;
            }
            QPushButton:pressed {
                background-color: #121215;
                color: #F87171;
            }
            """
        )
        self.exit_btn.clicked.connect(self._on_exit_clicked)
        self.controls_layout.addWidget(self.exit_btn)

        self.controls_layout.addStretch(1)

        self.hint_label = QLabel("Space / Arrows")
        self.hint_label.setStyleSheet("color: #63636E; font-size: 7.5pt;")
        self.controls_layout.addWidget(self.hint_label)

        layout.addLayout(self.controls_layout)

    def _on_score_changed(self, score: int, high_score: int):
        self.score_label.setText(f"{score} | Best: {high_score}")

    def _on_state_changed(self, state: str):
        if state == STATE_PLAYING:
            self.play_btn.setText("⏸ Pause")
            self.exit_btn.show()
        elif state == STATE_PAUSED:
            self.play_btn.setText("▶ Resume")
            self.exit_btn.show()
        elif state == STATE_GAME_OVER:
            self.play_btn.setText("↺ Play Again")
            self.exit_btn.show()
        else:
            self.play_btn.setText("▶ Play")
            self.exit_btn.show()

        self.state_changed.emit(state)

    def _toggle_play(self):
        self.canvas.setFocus()
        self.canvas.toggle_pause()

    def _on_exit_clicked(self):
        self.canvas.pause_game()
        self.exit_requested.emit()


# Auto-register Snake into ArcadeRegistry
def _register_snake_game():
    try:
        from gui.widgets.arcade import ArcadeGameInfo, ArcadeRegistry
        ArcadeRegistry.register(
            ArcadeGameInfo(
                game_id="snake",
                title="Snake",
                description="Classic grid crawler. Eat food, grow, avoid walls.",
                icon="🐍",
                author="Atlas",
            ),
            factory=lambda parent=None: AtlasSnakeCard(parent),
        )
    except Exception:
        pass


_register_snake_game()

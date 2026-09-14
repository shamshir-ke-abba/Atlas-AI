"""
Atlas V3 Canonical State Animation Widget.

Provides restrained, brand-aligned trajectory/node state animation for:
- Thinking (canonical teal trajectory)
- Using Tool (semantic blue trajectory)
- Searching (semantic blue trajectory)
- Responding / Generating (active teal trajectory)
- Success (green confirmation mark)
- Error (red semantic state)
- Offline (muted static state)

Respects reduced-motion preferences: when reduced motion is active, displays
static canonical SVGs without repeating timers or motion.
"""

from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from gui.theme import is_reduced_motion


ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"

STATE_SVGS = {
    "thinking": "atlas_mark_thinking.svg",
    "generating": "atlas_mark_thinking.svg",
    "responding": "atlas_mark_thinking.svg",
    "tool": "atlas_mark_tool.svg",
    "searching": "atlas_mark_tool.svg",
    "success": "atlas_mark_success.svg",
    "error": "atlas_mark_error.svg",
    "offline": "atlas_mark_offline.svg",
}

STATE_COLORS = {
    "thinking": "#4FB8BA",    # canonical teal
    "generating": "#4FB8BA",
    "responding": "#4FB8BA",
    "tool": "#60A5FA",        # semantic info blue
    "searching": "#60A5FA",
    "success": "#4ADE80",     # semantic green
    "error": "#F87171",       # semantic red
    "offline": "#82828C",     # muted
}


class TrajectoryTrack(QWidget):
    """Subtle 3-node trajectory indicator that smoothly advances in an ~1000ms loop."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(40, 16)
        self.setObjectName("TrajectoryTrack")
        self._phase = 0.0  # 0.0 to 1.0
        self._color = QColor("#4FB8BA")
        self._timer = QTimer(self)
        self._timer.setInterval(70)  # ~14 frames per sec, low overhead
        self._timer.timeout.connect(self._tick)

    def set_color(self, color_hex: str):
        self._color = QColor(color_hex)
        self.update()

    def start_animation(self):
        if is_reduced_motion():
            self._timer.stop()
            self._phase = 0.5
            self.update()
            return
        if not self._timer.isActive():
            self._phase = 0.0
            self._timer.start()

    def stop_animation(self):
        if self._timer.isActive():
            self._timer.stop()
        self._phase = 0.0
        self.update()

    def _tick(self):
        if is_reduced_motion():
            self.stop_animation()
            return
        self._phase = (self._phase + 0.07) % 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Baseline trajectory connection line
        line_pen = QPen(QColor("#27272F"), 1.2)
        line_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(line_pen)
        painter.drawLine(QPointF(6, 8), QPointF(34, 8))

        # 3 sequential trajectory nodes
        node_x = [6.0, 20.0, 34.0]
        radius = 2.4

        for i, cx in enumerate(node_x):
            if is_reduced_motion():
                alpha = 0.5
            else:
                # Calculate node activity based on circular phase
                target_phase = i / 2.0  # 0.0, 0.5, 1.0
                dist = abs(self._phase - target_phase)
                dist = min(dist, 1.0 - dist)
                # Soft pulse around target phase
                intensity = max(0.0, 1.0 - dist * 3.2)
                alpha = 0.25 + 0.75 * intensity

            c = QColor(self._color)
            c.setAlphaF(min(1.0, max(0.15, alpha)))
            painter.setBrush(c)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, 8.0), radius, radius)


class AtlasStateIndicator(QWidget):
    """Canonical Atlas trajectory/node state indicator for chat and status surfaces."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("AtlasStateIndicator")
        self._current_state = "thinking"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        self.icon_label = QLabel()
        self.icon_label.setObjectName("StateIcon")
        self.icon_label.setFixedSize(18, 18)
        layout.addWidget(self.icon_label)

        self.label = QLabel("Thinking...")
        self.label.setObjectName("StateLabel")
        layout.addWidget(self.label)

        self.track = TrajectoryTrack(self)
        layout.addWidget(self.track)
        layout.addStretch(1)

        self.set_state("thinking", "Thinking")

    def set_state(self, kind: str, text: str = ""):
        kind = str(kind).lower().strip()
        self._current_state = kind
        svg_filename = STATE_SVGS.get(kind, "atlas_mark_thinking.svg")
        svg_path = ASSETS_DIR / svg_filename
        if not svg_path.exists():
            svg_path = ASSETS_DIR / "atlas_mark.svg"

        if svg_path.exists():
            pix = QIcon(str(svg_path)).pixmap(18, 18)
            if not pix.isNull():
                self.icon_label.setPixmap(pix)

        color = STATE_COLORS.get(kind, "#4FB8BA")
        self.track.set_color(color)

        display_text = text or kind.replace("_", " ").title()
        self.label.setText(display_text)
        self.label.setStyleSheet(f"color: {color}; font-weight: 500; font-size: 10.5pt;")

        if kind in ("thinking", "generating", "responding", "tool", "searching"):
            self.track.show()
            self.track.start_animation()
        else:
            self.track.stop_animation()
            self.track.hide()

    def stop(self):
        self.track.stop_animation()

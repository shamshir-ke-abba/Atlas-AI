"""Atlas V3 Tool Workspace.

Brings native tools (Calculator, Calendar, Time, Fitness, Nutrition, Web Search, Math)
into alignment with the canonical Atlas V1 design system.
"""

from __future__ import annotations

from datetime import datetime
import math

from PySide6.QtCore import (
    QDate,
    QObject,
    QPointF,
    QThread,
    QTimer,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QCalendarWidget,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.tool_executor import ToolExecutor
from gui.widgets.profile_setup import ProfileSetupCard


class ToolTask(QObject):
    """Execute a tool away from the GUI thread."""

    result = Signal(str)
    error = Signal(str)
    finished = Signal()

    def __init__(self, executor, name, prompt):
        super().__init__()
        self.executor = executor
        self.name = name
        self.prompt = prompt

    @Slot()
    def run(self):
        try:
            result = self.executor.execute(self.name, self.prompt)
            self.result.emit(str(result or ""))
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


class AnalogClock(QWidget):
    """Restrained analog clock using canonical Atlas theme tokens."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update)
        self.timer.start()

    def paintEvent(self, event):
        now = datetime.now()
        side = min(self.width(), self.height()) - 16
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = side / 2

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dial face & border
        painter.setPen(QPen(QColor("#3F3F4A"), 1.5))
        painter.setBrush(QColor("#121215"))
        painter.drawEllipse(center, radius, radius)

        # Hour ticks
        painter.setPen(QPen(QColor("#82828C"), 1.5))
        for hour in range(12):
            rad = math.radians(hour * 30 - 90)
            outer = QPointF(
                center.x() + radius * 0.88 * math.cos(rad),
                center.y() + radius * 0.88 * math.sin(rad),
            )
            inner = QPointF(
                center.x() + radius * 0.78 * math.cos(rad),
                center.y() + radius * 0.78 * math.sin(rad),
            )
            painter.drawLine(inner, outer)

        second = now.second + now.microsecond / 1_000_000
        minute = now.minute + second / 60
        hour = (now.hour % 12) + minute / 60

        def draw_hand(angle, length, width, color):
            rad = math.radians(angle - 90)
            end = QPointF(
                center.x() + radius * length * math.cos(rad),
                center.y() + radius * length * math.sin(rad),
            )
            painter.setPen(QPen(color, width, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(center, end)

        # Hour and minute hands
        draw_hand(hour * 30, 0.50, 4.0, QColor("#F4F4F5"))
        draw_hand(minute * 6, 0.70, 2.5, QColor("#F4F4F5"))
        # Second hand (brand teal)
        draw_hand(second * 6, 0.82, 1.5, QColor("#398C8F"))

        # Center hub
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#4FB8BA")))
        painter.drawEllipse(center, 4, 4)
        painter.end()


class CalculatorWidget(QWidget):
    def __init__(self, plugin, parent: QWidget | None = None):
        super().__init__(parent)
        self.plugin = plugin
        self.expression = ""
        self.build_ui()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(12)

        container = QWidget()
        container.setMaximumWidth(440)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(10)

        title = QLabel("Calculator")
        title.setObjectName("ToolTitle")
        c_layout.addWidget(title)

        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setMinimumHeight(52)
        self.display.setObjectName("CalculatorDisplay")
        c_layout.addWidget(self.display)

        grid = QGridLayout()
        grid.setSpacing(6)

        keys = [
            ("C", 0, 0), ("⌫", 0, 1), ("(", 0, 2), (")", 0, 3),
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("÷", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("×", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("−", 3, 3),
            ("0", 4, 0), (".", 4, 1), ("^", 4, 2), ("+", 4, 3),
        ]

        for label, row, col in keys:
            button = QPushButton(label)
            button.setObjectName("CalculatorKey")
            button.setMinimumHeight(42)
            button.clicked.connect(
                lambda checked=False, value=label: self.press(value)
            )
            grid.addWidget(button, row, col)

        equals = QPushButton("=")
        equals.setObjectName("CalculatorEquals")
        equals.setMinimumHeight(42)
        equals.clicked.connect(self.calculate)
        grid.addWidget(equals, 5, 0, 1, 4)

        c_layout.addLayout(grid)
        root.addWidget(container, 0, Qt.AlignHCenter)
        root.addStretch(1)

    def press(self, value):
        if value == "C":
            self.expression = ""
        elif value == "⌫":
            self.expression = self.expression[:-1]
        else:
            value = {"÷": "/", "×": "*", "−": "-"}.get(value, value)
            self.expression += value
        self.display.setText(self.expression)

    def calculate(self):
        if not self.expression.strip():
            return
        try:
            result = self.plugin.run(expression=self.expression)
        except Exception as exc:
            result = str(exc)
        self.display.setText(str(result))
        self.expression = str(result)


class CalendarWidget(QWidget):
    def __init__(self, plugin=None, parent: QWidget | None = None):
        super().__init__(parent)
        self.plugin = plugin

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(12)

        container = QWidget()
        container.setMaximumWidth(520)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(10)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.setMinimumHeight(320)
        c_layout.addWidget(self.calendar)

        card = QFrame()
        card.setObjectName("DateInfoCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)

        self.info = QLabel()
        self.info.setAlignment(Qt.AlignCenter)
        self.info.setObjectName("DateInfo")
        card_layout.addWidget(self.info)

        c_layout.addWidget(card)
        root.addWidget(container, 0, Qt.AlignHCenter)
        root.addStretch(1)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def refresh(self):
        now = datetime.now()
        self.calendar.setSelectedDate(QDate(now.year, now.month, now.day))
        self.info.setText(
            f"{now.strftime('%A')}  •  "
            f"{now.strftime('%d %B %Y')}  •  "
            f"{now.strftime('%I:%M:%S %p')}"
        )


class TimeView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(12)

        container = QWidget()
        container.setMaximumWidth(440)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(8)

        self.clock = AnalogClock()
        c_layout.addWidget(self.clock, 0, alignment=Qt.AlignCenter)

        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setObjectName("TimeLabel")
        c_layout.addWidget(self.time_label)

        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setObjectName("DateInfo")
        c_layout.addWidget(self.date_label)

        root.addWidget(container, 0, Qt.AlignHCenter)
        root.addStretch(1)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def refresh(self):
        now = datetime.now()
        self.time_label.setText(now.strftime("%I:%M:%S %p"))
        self.date_label.setText(now.strftime("%A • %d %B %Y"))


class PromptToolWidget(QWidget):
    """Prompt-driven tool with a stable, non-overlapping landing state."""

    def __init__(self, controller, metadata, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        self.metadata = dict(metadata)
        self.executor = ToolExecutor(controller)
        self.task_thread = None
        self.task_worker = None
        self.run_button = None
        self.build_ui()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(10)

        scroll = QScrollArea()
        scroll.setObjectName("ToolScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)

        self.landing = QWidget()
        landing_root = QVBoxLayout(self.landing)
        landing_root.setContentsMargins(0, 8, 0, 8)
        landing_root.setSpacing(0)
        landing_root.addStretch(1)

        card = QFrame()
        card.setObjectName("ToolLandingCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        card.setMaximumWidth(580)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(8)

        icon = QLabel(str(self.metadata.get("icon", "🧩")))
        icon.setAlignment(Qt.AlignCenter)
        icon.setObjectName("ToolLandingIcon")
        card_layout.addWidget(icon)

        title = QLabel(str(self.metadata.get("display_name", "Atlas Tool")))
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("ToolLandingTitle")
        title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        card_layout.addWidget(title)

        desc = QLabel(str(self.metadata.get("description", "")))
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        desc.setObjectName("ToolLandingDescription")
        card_layout.addWidget(desc)

        hint = QLabel("Use the prompt below to run this tool.")
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        hint.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        hint.setObjectName("ToolLandingHint")
        card_layout.addWidget(hint)

        landing_root.addWidget(card, 0, Qt.AlignHCenter)
        landing_root.addStretch(1)
        scroll_layout.addWidget(self.landing, 1)

        self.result = QTextBrowser()
        self.result.setObjectName("ToolResultBrowser")
        self.result.setOpenExternalLinks(True)
        self.result.setFrameShape(QFrame.NoFrame)
        self.result.setMinimumHeight(200)
        self.result.hide()
        scroll_layout.addWidget(self.result, 1)

        scroll.setWidget(scroll_widget)
        root.addWidget(scroll, 1)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.prompt = QLineEdit()
        self.prompt.setObjectName("ToolPromptInput")
        self.prompt.setMinimumHeight(40)
        self.prompt.setPlaceholderText(self.placeholder())
        self.prompt.returnPressed.connect(self.submit)

        self.run_button = QPushButton("Run")
        self.run_button.setObjectName("ToolRunButton")
        self.run_button.setMinimumHeight(40)
        self.run_button.clicked.connect(self.submit)

        row.addWidget(self.prompt, 1)
        row.addWidget(self.run_button)
        root.addLayout(row)

    def placeholder(self):
        examples = {
            "math": "e.g. integrate 2x**2 + 4",
            "web_search": "e.g. When is India's Independence Day?",
        }
        return examples.get(
            self.metadata.get("name", ""),
            "Enter a prompt...",
        )

    def submit(self):
        prompt = self.prompt.text().strip()
        if not prompt or self.task_thread is not None:
            return

        self.landing.hide()
        self.result.show()
        self.result.setMarkdown("**Running…**\n\nAtlas is executing this tool in the background.")
        self.prompt.setEnabled(False)
        self.run_button.setEnabled(False)

        self.task_thread = QThread(self)
        self.task_worker = ToolTask(
            self.executor,
            self.metadata.get("name"),
            prompt,
        )
        self.task_worker.moveToThread(self.task_thread)
        self.task_thread.started.connect(self.task_worker.run)
        self.task_worker.result.connect(self._tool_result)
        self.task_worker.error.connect(self._tool_error)
        self.task_worker.finished.connect(self.task_thread.quit)
        self.task_worker.finished.connect(self.task_worker.deleteLater)
        self.task_thread.finished.connect(self._tool_thread_finished)
        self.task_thread.finished.connect(self.task_thread.deleteLater)
        self.task_thread.start()

    def _tool_result(self, result):
        self.result.setMarkdown(str(result or "No result returned."))

    def _tool_error(self, error):
        self.result.setMarkdown(f"### Tool Error\n\n{error}")

    def _tool_thread_finished(self):
        self.task_worker = None
        self.task_thread = None
        self.prompt.setEnabled(True)
        self.run_button.setEnabled(True)
        self.prompt.clear()
        self.prompt.setFocus()


class ProfileToolView(QWidget):
    """Real profile + action surface backed by the actual plugin."""

    def __init__(self, tool, controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.tool = str(tool).lower().strip()
        self.controller = controller

        scroll = QScrollArea()
        scroll.setObjectName("ToolScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        container.setMaximumWidth(640)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(32, 20, 32, 24)
        c_layout.setSpacing(14)

        self.card = ProfileSetupCard(self.tool, controller=controller)
        self.card.submitted.connect(self.profile_saved)
        c_layout.addWidget(self.card)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        if self.tool == "fitness":
            action_specs = [
                ("Generate workout", "generate_workout"),
                ("Exercises", "get_exercises"),
                ("Rep guidance", "rep_guidance"),
            ]
        else:
            action_specs = [
                ("Generate meal plan", "generate_meal_plan"),
                ("View current plan", "get_meal_plan"),
            ]

        for label, action in action_specs:
            button = QPushButton(label)
            button.setObjectName("ToolActionButton")
            button.setMinimumHeight(38)
            button.clicked.connect(
                lambda checked=False, a=action: self.run_action(a)
            )
            actions.addWidget(button)
        c_layout.addLayout(actions)

        self.result = QTextBrowser()
        self.result.setObjectName("ToolResultBrowser")
        self.result.setOpenExternalLinks(True)
        self.result.setMinimumHeight(180)
        self.result.setPlaceholderText("Tool results will appear here.")
        c_layout.addWidget(self.result)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addWidget(container, 0, Qt.AlignHCenter)
        scroll.setWidget(scroll_content)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(scroll, 1)

    def profile_saved(self, tool, profile):
        if tool != self.tool:
            return
        self.result.setMarkdown(
            "**Profile saved.** The backend plugin now has your profile and "
            "can use it for the actions below."
        )

    def run_action(self, action):
        try:
            result = self.controller.run_tool_action(self.tool, action)
            self.result.setMarkdown(str(result or "No result returned."))
        except Exception as exc:
            self.result.setMarkdown(f"### Tool Error\n\n{exc}")


class CodingToolWidget(QWidget):
    """Native Coding Agent surface connecting to the existing agents.coding backend."""

    def __init__(self, controller, metadata, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        self.metadata = dict(metadata)
        self._is_running = False
        self.build_ui()
        self._connect_signals()

    def _connect_signals(self):
        ai = getattr(self.controller, "ai", None)
        if ai is not None:
            if hasattr(ai, "coding_result"):
                ai.coding_result.connect(self._on_coding_result)
            if hasattr(ai, "coding_error"):
                ai.coding_error.connect(self._on_coding_error)
            if hasattr(ai, "coding_finished"):
                ai.coding_finished.connect(self._on_coding_finished)

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(10)

        scroll = QScrollArea()
        scroll.setObjectName("ToolScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)

        self.landing = QWidget()
        landing_root = QVBoxLayout(self.landing)
        landing_root.setContentsMargins(0, 8, 0, 8)
        landing_root.setSpacing(0)
        landing_root.addStretch(1)

        card = QFrame()
        card.setObjectName("ToolLandingCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        card.setMaximumWidth(580)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(8)

        icon = QLabel("💻")
        icon.setAlignment(Qt.AlignCenter)
        icon.setObjectName("ToolLandingIcon")
        card_layout.addWidget(icon)

        title = QLabel("Coding Agent")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("ToolLandingTitle")
        title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        card_layout.addWidget(title)

        desc = QLabel(
            "Inspect repository files, plan code edits, apply changes, "
            "and run tests with permission approval."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        desc.setObjectName("ToolLandingDescription")
        card_layout.addWidget(desc)

        hint = QLabel("Describe a task below (e.g. 'Add unit test for helper', 'Fix bug in tokenizer').")
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        hint.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        hint.setObjectName("ToolLandingHint")
        card_layout.addWidget(hint)

        landing_root.addWidget(card, 0, Qt.AlignHCenter)
        landing_root.addStretch(1)
        scroll_layout.addWidget(self.landing, 1)

        self.result = QTextBrowser()
        self.result.setObjectName("ToolResultBrowser")
        self.result.setOpenExternalLinks(True)
        self.result.setFrameShape(QFrame.NoFrame)
        self.result.setMinimumHeight(240)
        self.result.hide()
        scroll_layout.addWidget(self.result, 1)

        scroll.setWidget(scroll_widget)
        root.addWidget(scroll, 1)

        status_row = QHBoxLayout()
        self.status_label = QLabel("Idle")
        self.status_label.setStyleSheet("color: #82828C; font-size: 9.5pt;")
        status_row.addWidget(self.status_label)
        status_row.addStretch(1)
        root.addLayout(status_row)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.prompt = QLineEdit()
        self.prompt.setObjectName("ToolPromptInput")
        self.prompt.setMinimumHeight(40)
        self.prompt.setPlaceholderText("Describe the coding task...")
        self.prompt.returnPressed.connect(self.submit)

        self.run_button = QPushButton("Run")
        self.run_button.setObjectName("ToolRunButton")
        self.run_button.setMinimumHeight(40)
        self.run_button.clicked.connect(self.submit)

        row.addWidget(self.prompt, 1)
        row.addWidget(self.run_button)
        root.addLayout(row)

    def submit(self):
        task = self.prompt.text().strip()
        if not task or self._is_running:
            return

        from gui.widgets.coding_permission_dialog import CodingPermissionDialog
        from agents.coding.permissions import CodingPermissions
        from PySide6.QtWidgets import QDialog

        dialog = CodingPermissionDialog(parent=self)
        if dialog.exec() != QDialog.Accepted:
            self.landing.hide()
            self.result.show()
            self.result.setMarkdown("### Task Cancelled\n\nCoding Agent task cancelled by user.")
            self.status_label.setText("Cancelled")
            return

        permissions = CodingPermissions(**dialog.permissions())

        self._is_running = True
        self.prompt.setEnabled(False)
        self.run_button.setEnabled(False)
        self.run_button.setText("Running...")
        self.status_label.setText("Running Coding Agent...")
        self.landing.hide()
        self.result.show()
        self.result.setMarkdown(
            f"**Running Coding Agent...**\n\n"
            f"**Task:** {task}\n\n"
            f"Atlas is inspecting repository files, planning changes, and running tests."
        )

        ai = getattr(self.controller, "ai", None)
        if ai is not None and hasattr(ai, "execute_coding"):
            ai.execute_coding(task, permissions, max_attempts=2)
        else:
            self._on_coding_error("Coding Agent AI service is not available.")

    def _on_coding_result(self, result):
        if result is None:
            self.result.setMarkdown("### Coding Agent\n\nNo result returned.")
            self.status_label.setText("Finished (no result)")
            return

        success = getattr(result, "success", False)
        message = getattr(result, "message", "")
        applied = getattr(result, "applied_changes", []) or []
        test_result = getattr(result, "test_result", {}) or {}
        error_analysis = getattr(result, "error_analysis", None)

        md = []
        if success:
            md.append("### ✓ Coding Task Completed Successfully\n")
            self.status_label.setText("✓ Success")
        else:
            md.append("### ⚠ Coding Task Incomplete\n")
            self.status_label.setText("⚠ Incomplete")

        if message:
            md.append(f"{message}\n")

        if applied:
            md.append("#### Modified Files\n")
            for f in applied:
                md.append(f"- `{f}`")
            md.append("")

        if test_result:
            md.append("#### Test Execution Summary\n")
            summary = test_result.get("summary", "")
            if summary:
                md.append(f"{summary}\n")
            tests_passed = test_result.get("passed", 0)
            tests_failed = test_result.get("failed", 0)
            md.append(f"Passed: **{tests_passed}** · Failed: **{tests_failed}**\n")

        if error_analysis is not None:
            err_type = getattr(error_analysis, "error_type", "")
            err_msg = getattr(error_analysis, "message", "")
            if err_type or err_msg:
                md.append(f"#### Error Details\n**Type:** {err_type}\n\n```\n{err_msg}\n```\n")

        self.result.setMarkdown("\n".join(md))

    def _on_coding_error(self, error):
        self.status_label.setText("Error")
        self.result.setMarkdown(f"### Coding Agent Error\n\n```\n{error}\n```")

    def _on_coding_finished(self):
        self._is_running = False
        self.prompt.setEnabled(True)
        self.run_button.setEnabled(True)
        self.run_button.setText("Run")
        self.prompt.clear()
        self.prompt.setFocus()


class ToolWorkspace(QWidget):
    def __init__(self, controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        self.stack = QStackedWidget()
        self.views = {}
        self.build_ui()
        self.refresh_tools()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header_bar = QWidget()
        self.header_bar.setObjectName("ToolHeaderBar")
        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(24, 12, 24, 12)
        header_layout.setSpacing(12)

        self.back_button = QPushButton("← Tools")
        self.back_button.setObjectName("ToolBackButton")
        self.back_button.clicked.connect(self.show_overview)
        self.back_button.hide()
        header_layout.addWidget(self.back_button)

        self.title = QLabel("Tools")
        self.title.setObjectName("ToolHeader")
        header_layout.addWidget(self.title)
        header_layout.addStretch()
        root.addWidget(self.header_bar)

        root.addWidget(self.stack, 1)

        self.overview = QWidget()
        overview_layout = QVBoxLayout(self.overview)
        overview_layout.setContentsMargins(24, 20, 24, 24)
        overview_layout.setSpacing(6)

        heading = QLabel("Atlas Tools")
        heading.setObjectName("ToolTitle")
        overview_layout.addWidget(heading)

        subtitle = QLabel("Open a tool to use its dedicated interface.")
        subtitle.setObjectName("ToolDescription")
        overview_layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setObjectName("ToolScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        container = QWidget()
        self.grid = QGridLayout(container)
        self.grid.setSpacing(12)
        scroll.setWidget(container)
        overview_layout.addWidget(scroll, 1)

        self.stack.addWidget(self.overview)

    def manager(self):
        return getattr(
            getattr(self.controller, "ai", None),
            "tools",
            None,
        )

    def refresh_tools(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        manager = self.manager()
        metadata = list(manager.metadata() if manager is not None else [])

        # Ensure Coding Agent is included in tool cards
        names = [str(m.get("name", "")).lower() for m in metadata if isinstance(m, dict)]
        if "coding" not in names:
            metadata.append({
                "name": "coding",
                "display_name": "Coding Agent",
                "icon": "💻",
                "description": "Autonomous coding agent for repository inspection, code editing, and test verification.",
                "enabled": True,
            })

        row = col = 0
        for data in metadata:
            if not isinstance(data, dict):
                continue

            card = QFrame()
            card.setObjectName("ToolCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(8)

            top = QHBoxLayout()
            icon = QLabel(str(data.get("icon", "🧩")))
            icon.setObjectName("ToolIcon")
            top.addWidget(icon)

            title = QLabel(
                str(data.get("display_name", data.get("name", "Tool")))
            )
            title.setObjectName("ToolCardTitle")
            top.addWidget(title)
            top.addStretch()
            layout.addLayout(top)

            desc = QLabel(str(data.get("description", "")))
            desc.setWordWrap(True)
            desc.setObjectName("ToolDescription")
            layout.addWidget(desc)

            button = QPushButton("Open")
            button.setObjectName("ToolOpenButton")
            button.setEnabled(bool(data.get("enabled", True)))
            button.clicked.connect(
                lambda checked=False, d=data: self.open_tool(d)
            )
            layout.addWidget(button)

            self.grid.addWidget(card, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1

    def open_tool(self, metadata):
        name = str(metadata.get("name", "")).lower()

        if name not in self.views:
            self.views[name] = self.create_view(metadata)
            self.stack.addWidget(self.views[name])

        self.back_button.show()
        self.title.setText(
            f"{metadata.get('icon', '🧩')}  "
            f"{metadata.get('display_name', name)}"
        )
        self.stack.setCurrentWidget(self.views[name])

    def create_view(self, metadata):
        name = metadata.get("name")
        manager = self.manager()
        plugin = manager.get(name) if manager else None

        if name == "calculator" and plugin is not None:
            return CalculatorWidget(plugin)

        if name == "calendar":
            return CalendarWidget(plugin)

        if name == "time":
            return TimeView()

        if name in ("fitness", "nutrition"):
            return ProfileToolView(
                name,
                self.controller,
            )

        if name == "coding":
            return CodingToolWidget(
                self.controller,
                metadata,
            )

        return PromptToolWidget(
            self.controller,
            metadata,
        )

    def show_overview(self):
        self.back_button.hide()
        self.title.setText("Tools")
        self.refresh_tools()
        self.stack.setCurrentWidget(self.overview)

"""
Atlas V3 Tool Workspace.

Calculator, Calendar and Time are visual tools. Fitness/Nutrition expose
interactive profiles. Web Search and Math use the same clean landing screen
until a prompt is entered.
"""

from datetime import datetime
import math

from PySide6.QtCore import Qt, QTimer, QPointF, Signal, QDate, QObject, Slot, QThread
from PySide6.QtGui import QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QCalendarWidget,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QSizePolicy,
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 250)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update)
        self.timer.start()

    def paintEvent(self, event):
        now = datetime.now()
        side = min(self.width(), self.height()) - 18
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = side / 2

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self.palette().text(), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, radius, radius)

        for hour in range(12):
            rad = math.radians(hour * 30 - 90)
            outer = QPointF(
                center.x() + radius * 0.88 * math.cos(rad),
                center.y() + radius * 0.88 * math.sin(rad),
            )
            inner = QPointF(
                center.x() + radius * 0.79 * math.cos(rad),
                center.y() + radius * 0.79 * math.sin(rad),
            )
            painter.drawLine(inner, outer)

        second = now.second + now.microsecond / 1_000_000
        minute = now.minute + second / 60
        hour = (now.hour % 12) + minute / 60

        def draw_hand(angle, length, width):
            rad = math.radians(angle - 90)
            end = QPointF(
                center.x() + radius * length * math.cos(rad),
                center.y() + radius * length * math.sin(rad),
            )
            painter.setPen(QPen(self.palette().text(), width))
            painter.drawLine(center, end)

        draw_hand(hour * 30, 0.50, 6)
        draw_hand(minute * 6, 0.69, 4)
        draw_hand(second * 6, 0.78, 2)

        painter.setBrush(QBrush(self.palette().text()))
        painter.drawEllipse(center, 5, 5)
        painter.end()


class CalculatorWidget(QWidget):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.expression = ""
        self.build_ui()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 28, 40, 28)
        root.setSpacing(12)

        title = QLabel("🧮 Calculator")
        title.setObjectName("ToolTitle")
        root.addWidget(title)

        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setMinimumHeight(58)
        self.display.setObjectName("CalculatorDisplay")
        root.addWidget(self.display)

        grid = QGridLayout()
        grid.setSpacing(8)

        keys = [
            ("C", 0, 0), ("⌫", 0, 1), ("(", 0, 2), (")", 0, 3),
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("÷", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("×", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("−", 3, 3),
            ("0", 4, 0), (".", 4, 1), ("^", 4, 2), ("+", 4, 3),
        ]

        for label, row, col in keys:
            button = QPushButton(label)
            button.setMinimumHeight(48)
            button.clicked.connect(
                lambda checked=False, value=label: self.press(value)
            )
            grid.addWidget(button, row, col)

        equals = QPushButton("=")
        equals.setMinimumHeight(48)
        equals.clicked.connect(self.calculate)
        grid.addWidget(equals, 5, 0, 1, 4)

        root.addLayout(grid)
        root.addStretch(1)

    def press(self, value):
        if value == "C":
            self.expression = ""
        elif value == "⌫":
            self.expression = self.expression[:-1]
        else:
            # Store ASCII operators; the plugin also accepts Unicode operators.
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
    def __init__(self, plugin=None, parent=None):
        super().__init__(parent)
        self.plugin = plugin

        root = QVBoxLayout(self)
        root.setContentsMargins(35, 20, 35, 20)
        root.setSpacing(10)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(
            QCalendarWidget.NoVerticalHeader
        )
        self.calendar.setSelectedDate(
            QDate.currentDate()
        )
        self.calendar.setMinimumHeight(370)
        root.addWidget(self.calendar)

        card = QFrame()
        card.setObjectName("DateInfoCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)

        self.info = QLabel()
        self.info.setAlignment(Qt.AlignCenter)
        self.info.setObjectName("DateInfo")
        card_layout.addWidget(self.info)

        root.addWidget(card)
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
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 20, 30, 20)
        root.setSpacing(6)

        self.clock = AnalogClock()
        root.addWidget(self.clock, 1, alignment=Qt.AlignCenter)

        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setObjectName("TimeLabel")
        root.addWidget(self.time_label)

        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setObjectName("DateInfo")
        root.addWidget(self.date_label)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def refresh(self):
        now = datetime.now()
        self.time_label.setText(now.strftime("%I:%M:%S %p"))
        self.date_label.setText(
            now.strftime("%A • %d %B %Y")
        )


class PromptToolWidget(QWidget):
    """Prompt-driven tool with a stable, non-overlapping landing state."""

    def __init__(self, controller, metadata, parent=None):
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
        root.setContentsMargins(32, 24, 32, 22)
        root.setSpacing(12)

        self.landing = QWidget()
        landing_root = QVBoxLayout(self.landing)
        landing_root.setContentsMargins(0, 8, 0, 8)
        landing_root.setSpacing(0)

        landing_root.addStretch(1)

        card = QFrame()
        card.setObjectName("ToolLandingCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        card.setMaximumWidth(720)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(42, 34, 42, 34)
        card_layout.setSpacing(10)

        icon = QLabel(str(self.metadata.get("icon", "🧩")))
        icon.setAlignment(Qt.AlignCenter)
        icon.setMinimumHeight(64)
        icon.setStyleSheet("font-size:46px; background:transparent;")
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
        desc.setMinimumHeight(max(24, desc.sizeHint().height()))
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
        root.addWidget(self.landing, 1)

        self.result = QTextBrowser()
        self.result.setOpenExternalLinks(True)
        self.result.setFrameShape(QFrame.NoFrame)
        self.result.hide()
        root.addWidget(self.result, 1)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.prompt = QLineEdit()
        self.prompt.setMinimumHeight(42)
        self.prompt.setPlaceholderText(self.placeholder())
        self.prompt.returnPressed.connect(self.submit)

        self.run_button = QPushButton("Run")
        self.run_button.setMinimumHeight(42)
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

    def __init__(self, tool, controller, parent=None):
        super().__init__(parent)
        self.tool = str(tool).lower().strip()
        self.controller = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(45, 25, 45, 25)
        root.setSpacing(12)

        self.card = ProfileSetupCard(self.tool, controller=controller)
        self.card.submitted.connect(self.profile_saved)
        root.addWidget(self.card)

        actions = QHBoxLayout()
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
            button.clicked.connect(
                lambda checked=False, a=action: self.run_action(a)
            )
            actions.addWidget(button)
        root.addLayout(actions)

        self.result = QTextBrowser()
        self.result.setOpenExternalLinks(True)
        self.result.setMinimumHeight(150)
        self.result.setPlaceholderText("Tool results will appear here.")
        root.addWidget(self.result, 1)

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


class ToolWorkspace(QWidget):
    def __init__(self, controller, parent=None):
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

        header = QHBoxLayout()
        header.setContentsMargins(20, 15, 20, 10)

        back = QPushButton("← Tools")
        back.clicked.connect(self.show_overview)
        header.addWidget(back)

        self.title = QLabel("Tools")
        self.title.setObjectName("ToolHeader")
        header.addWidget(self.title)
        header.addStretch()
        root.addLayout(header)

        root.addWidget(self.stack, 1)

        self.overview = QWidget()
        overview_layout = QVBoxLayout(self.overview)
        overview_layout.setContentsMargins(28, 18, 28, 28)

        heading = QLabel("Atlas Tools")
        heading.setObjectName("ToolTitle")
        overview_layout.addWidget(heading)

        subtitle = QLabel(
            "Open a tool to use its dedicated interface."
        )
        subtitle.setObjectName("ToolDescription")
        overview_layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        container = QWidget()
        self.grid = QGridLayout(container)
        self.grid.setSpacing(14)
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
        metadata = manager.metadata() if manager is not None else []

        row = col = 0
        for data in metadata:
            if not isinstance(data, dict):
                continue

            card = QFrame()
            card.setObjectName("ToolCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(18, 18, 18, 18)
            layout.setSpacing(7)

            top = QHBoxLayout()
            icon = QLabel(str(data.get("icon", "🧩")))
            icon.setStyleSheet("font-size:26px;")
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

        return PromptToolWidget(
            self.controller,
            metadata,
        )

    def show_overview(self):
        self.title.setText("Tools")
        self.refresh_tools()
        self.stack.setCurrentWidget(self.overview)

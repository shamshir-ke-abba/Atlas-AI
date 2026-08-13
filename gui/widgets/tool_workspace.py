"""
Atlas Tool Workspace

Hosts the GUI for individual Atlas tools.

Calculator mathematics is handled directly by
Atlas MathEngine instead of the LLM.
"""

from PySide6.QtCore import Qt, Signal

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from plugins.math_engine.engine import MathEngine


# ==========================================================
# Generic Tool View
# ==========================================================

class GenericToolView(QWidget):

    def __init__(
        self,
        metadata,
        parent=None,
    ):

        super().__init__(
            parent
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            40,
            40,
            40,
            40,
        )

        icon = QLabel(
            metadata.get(
                "icon",
                "🧩",
            )
        )

        icon.setAlignment(
            Qt.AlignCenter
        )

        icon.setStyleSheet(
            "font-size: 48px;"
        )

        title = QLabel(
            metadata.get(
                "display_name",
                "Tool",
            )
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setObjectName(
            "ToolTitle"
        )

        description = QLabel(
            metadata.get(
                "description",
                "Atlas tool.",
            )
        )

        description.setAlignment(
            Qt.AlignCenter
        )

        description.setWordWrap(
            True
        )

        description.setObjectName(
            "ToolDescription"
        )

        layout.addStretch()

        layout.addWidget(
            icon
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            description
        )

        layout.addStretch()


# ==========================================================
# Calculator View
# ==========================================================

class CalculatorView(QWidget):

    def __init__(
        self,
        controller,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.controller = controller

        # ==================================================
        # Dedicated Math Engine
        # ==================================================

        self.math = MathEngine()

        # ==================================================
        # Current Math State
        # ==================================================

        self.current_expression = ""

        self.current_result = ""

        self.build_ui()

    # ======================================================
    # UI
    # ======================================================

    def build_ui(self):

        root = QHBoxLayout(
            self
        )

        root.setContentsMargins(
            30,
            30,
            30,
            30,
        )

        root.setSpacing(
            20
        )

        # ==================================================
        # Calculator Panel
        # ==================================================

        calculator_panel = QFrame()

        calculator_panel.setObjectName(
            "ToolPanel"
        )

        calculator_layout = QVBoxLayout(
            calculator_panel
        )

        calculator_layout.setContentsMargins(
            25,
            25,
            25,
            25,
        )

        title = QLabel(
            "🧮 Calculator"
        )

        title.setObjectName(
            "ToolTitle"
        )

        calculator_layout.addWidget(
            title
        )

        # ==================================================
        # Display
        # ==================================================

        self.display = QLineEdit()

        self.display.setPlaceholderText(
            "Enter expression..."
        )

        self.display.setObjectName(
            "CalculatorDisplay"
        )

        self.display.returnPressed.connect(
            self.calculate
        )

        calculator_layout.addWidget(
            self.display
        )

        # ==================================================
        # Buttons
        # ==================================================

        buttons = [
            "7", "8", "9", "/",
            "4", "5", "6", "*",
            "1", "2", "3", "-",
            "0", ".", "(", ")",
            "C", "^", "=", "+"
        ]

        grid = QGridLayout()

        for index, text in enumerate(
            buttons
        ):

            button = QPushButton(
                text
            )

            button.setMinimumHeight(
                50
            )

            button.clicked.connect(
                lambda checked=False,
                value=text:
                self.button_pressed(
                    value
                )
            )

            row = index // 4
            column = index % 4

            grid.addWidget(
                button,
                row,
                column,
            )

        calculator_layout.addLayout(
            grid
        )

        # ==================================================
        # Atlas Explanation Panel
        # ==================================================

        chat_panel = QFrame()

        chat_panel.setObjectName(
            "ToolPanel"
        )

        chat_layout = QVBoxLayout(
            chat_panel
        )

        chat_title = QLabel(
            "Atlas Math"
        )

        chat_title.setObjectName(
            "ToolTitle"
        )

        chat_layout.addWidget(
            chat_title
        )

        # ==================================================
        # Explanation
        # ==================================================

        self.explanation = QTextEdit()

        self.explanation.setReadOnly(
            True
        )

        self.explanation.setPlaceholderText(
            "Atlas can explain the calculation here."
        )

        chat_layout.addWidget(
            self.explanation,
            1,
        )

        # ==================================================
        # Question
        # ==================================================

        self.question = QLineEdit()

        self.question.setPlaceholderText(
            "Ask about this calculation..."
        )

        self.question.returnPressed.connect(
            self.ask_atlas
        )

        chat_layout.addWidget(
            self.question
        )

        # ==================================================
        # Ask Button
        # ==================================================

        self.ask_button = QPushButton(
            "Explain"
        )

        self.ask_button.clicked.connect(
            self.ask_atlas
        )

        chat_layout.addWidget(
            self.ask_button
        )

        # ==================================================
        # Add Panels
        # ==================================================

        root.addWidget(
            calculator_panel,
            1,
        )

        root.addWidget(
            chat_panel,
            1,
        )

    # ======================================================
    # Button Handling
    # ======================================================

    def button_pressed(
        self,
        value,
    ):

        # --------------------------------------------------
        # Clear
        # --------------------------------------------------

        if value == "C":

            self.display.clear()

            self.current_expression = ""
            self.current_result = ""

            self.explanation.clear()

            return

        # --------------------------------------------------
        # Equals
        # --------------------------------------------------

        if value == "=":

            self.calculate()

            return

        # --------------------------------------------------
        # Power
        # --------------------------------------------------

        if value == "^":

            value = "^"

        self.display.insert(
            value
        )

    # ======================================================
    # Calculate
    # ======================================================

    def calculate(self):

        expression = (
            self.display.text()
            .strip()
        )

        if not expression:

            return

        try:

            result = self.math.calculate(
                expression
            )

            result_text = self.math.format(
                result
            )

            # ==================================================
            # Replace active context
            # ==================================================

            self.current_expression = (
                expression
            )

            self.current_result = (
                result_text
            )

            # ==================================================
            # Keep expression visible
            # ==================================================

            self.display.setText(
                expression
            )

            # ==================================================
            # Display result
            # ==================================================

            self.explanation.setMarkdown(
                "### Result\n\n"
                f"**Expression**\n\n"
                f"`{expression}`\n\n"
                "**Answer**\n\n"
                f"**{result_text}**\n\n"
                "Ask Atlas Math to explain it."
            )

        except Exception as error:

            self.current_expression = ""
            self.current_result = ""

            self.explanation.setMarkdown(
                "### Calculation Error\n\n"
                f"`{error}`"
            )

    # ======================================================
    # Ask Atlas Math
    # ======================================================

    def ask_atlas(self):

        question = (
            self.question.text()
            .strip()
        )

        if not question:

            return

        expression = (
            self.current_expression
            .strip()
        )

        result = (
            self.current_result
            .strip()
        )

        # ==================================================
        # No existing calculation
        # ==================================================

        if not expression:

            # --------------------------------------------------
            # Try to extract an expression directly from
            # the user's question.
            # --------------------------------------------------

            extracted = (
                self.math.extract_expression(
                    question
                )
            )

            if extracted:

                expression = extracted

            else:

                self.explanation.setMarkdown(
                    "### No calculation\n\n"
                    "Enter a calculation first, "
                    "or ask a mathematical question "
                    "containing an expression."
                )

                return

        # ==================================================
        # Disable UI while calculating
        #
        # This is extremely fast because it is SymPy,
        # not Qwen.
        # ==================================================

        self.ask_button.setEnabled(
            False
        )

        self.question.setEnabled(
            False
        )

        self.explanation.setMarkdown(
            "### Atlas Math\n\n"
            "Calculating..."
        )

        try:

            response = self.math.explain(
                question,
                expression,
                result,
            )

            # --------------------------------------------------
            # If the question contained a NEW expression,
            # update the active state.
            # --------------------------------------------------

            new_expression = (
                self.math.extract_expression(
                    question,
                    fallback="",
                )
            )

            if new_expression:

                self.current_expression = (
                    new_expression
                )

                try:

                    new_result = (
                        self.math.calculate(
                            new_expression
                        )
                    )

                    self.current_result = (
                        self.math.format(
                            new_result
                        )
                    )

                except Exception:

                    pass

            self.explanation.setMarkdown(
                response
            )

        except Exception as error:

            self.explanation.setMarkdown(
                "### Math Error\n\n"
                f"{error}"
            )

        finally:

            self.ask_button.setEnabled(
                True
            )

            self.question.setEnabled(
                True
            )

            self.question.clear()

            self.question.setFocus()


# ==========================================================
# Tool Workspace
# ==========================================================

class ToolWorkspace(QWidget):

    tool_closed = Signal()

    def __init__(
        self,
        controller,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.controller = controller

        self.tools = {}

        self.build_ui()

    # ======================================================
    # UI
    # ======================================================

    def build_ui(self):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            0
        )

        # ==================================================
        # Header
        # ==================================================

        header = QHBoxLayout()

        header.setContentsMargins(
            20,
            15,
            20,
            15,
        )

        self.back_button = QPushButton(
            "← Tools"
        )

        self.back_button.clicked.connect(
            self.close_tool
        )

        header.addWidget(
            self.back_button
        )

        self.title = QLabel(
            "Tool"
        )

        self.title.setObjectName(
            "ToolHeader"
        )

        header.addWidget(
            self.title
        )

        header.addStretch()

        layout.addLayout(
            header
        )

        # ==================================================
        # Tool Stack
        # ==================================================

        self.stack = QStackedWidget()

        layout.addWidget(
            self.stack,
            1,
        )

    # ======================================================
    # Open Tool
    # ======================================================

    def open_tool(
        self,
        metadata,
    ):

        name = metadata.get(
            "name"
        )

        if not name:

            return

        display_name = metadata.get(
            "display_name",
            name,
        )

        icon = metadata.get(
            "icon",
            "🧩",
        )

        self.title.setText(
            f"{icon}  {display_name}"
        )

        # ==================================================
        # Create View Only Once
        # ==================================================

        if name not in self.tools:

            gui_id = metadata.get(
                "gui_id",
                "generic",
            )

            if gui_id == "calculator":

                view = CalculatorView(
                    self.controller
                )

            else:

                view = GenericToolView(
                    metadata
                )

            self.tools[name] = view

            self.stack.addWidget(
                view
            )

        # ==================================================
        # Show Tool
        # ==================================================

        self.stack.setCurrentWidget(
            self.tools[name]
        )

    # ======================================================
    # Close Tool
    # ======================================================

    def close_tool(self):

        self.tool_closed.emit()
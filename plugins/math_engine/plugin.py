"""
Atlas V3 Math Plugin.
"""

import re

from plugins.base import AtlasPlugin
from plugins.math_engine.engine import MathEngine


class MathPlugin(AtlasPlugin):
    name = "math"
    display_name = "Mathematics"
    description = (
        "Symbolic mathematics: calculation, differentiation, integration, "
        "simplification, expansion, factorization and equation solving."
    )
    icon = "∑"
    has_gui = True
    gui_id = "math"
    priority = 5

    triggers = [
        "differentiate",
        "diffrentiate",
        "derivative",
        "integrate",
        "integral",
        "simplify",
        "factor",
        "factorize",
        "factorise",
        "expand",
        "solve",
        "equation",
    ]

    def __init__(self):
        super().__init__()
        self.engine = MathEngine()

    def detect_operation(self, message):
        return self.engine.detect_operation(message)

    def extract_expression(self, message, operation=None):
        return self.engine.extract_expression(
            message,
            operation,
        )

    def detect_variable(self, text, expression=""):
        patterns = (
            r"\bwith\s+respect\s+to\s+([a-zA-Z_]\w*)",
            r"\brespect\s+to\s+([a-zA-Z_]\w*)",
            r"\bwrt\s+([a-zA-Z_]\w*)",
        )

        for pattern in patterns:
            match = re.search(
                pattern,
                str(text),
                flags=re.IGNORECASE,
            )
            if match:
                return match.group(1)

        expression = str(expression or "")
        for symbol in self.engine.SYMBOL_NAMES:
            if re.search(
                rf"\b{re.escape(symbol)}\b",
                expression,
            ):
                return symbol

        return "x"

    def can_handle(self, message):
        text = str(message or "").strip()
        if not text:
            return False

        operation = self.detect_operation(text)
        if operation is None or operation == "calculate":
            return False

        expression = self.extract_expression(
            text,
            operation,
        )
        if not expression:
            return False

        try:
            self.engine._validate_expression(expression)
            return True
        except Exception:
            return False

    def run(
        self,
        expression="",
        operation="",
        variable="x",
        **kwargs,
    ):
        request = str(expression or "").strip()

        if not request:
            return (
                "### Math Error\n\n"
                "Please provide a mathematical expression."
            )

        operation = operation or self.detect_operation(request)

        if operation is None:
            return (
                "### Math Error\n\n"
                "Please specify an operation such as integrate "
                "or differentiate."
            )

        math_expression = self.extract_expression(
            request,
            operation,
        )

        variable = variable or self.detect_variable(
            request,
            math_expression,
        )

        try:
            result = self.engine.execute(
                operation,
                math_expression,
                variable,
            )
            formatted = self.engine.format(result)

            if str(operation).lower() in ("integrate", "integral"):
                formatted = f"{formatted} + C"

            return (
                "### Atlas Math\n\n"
                "**Expression**\n\n"
                f"`{math_expression}`\n\n"
                "**Answer**\n\n"
                f"{formatted}"
            )

        except Exception as exc:
            return f"### Math Error\n\n{exc}"

    def explain(
        self,
        question,
        expression="",
        result="",
        variable="x",
    ):
        return self.engine.explain(
            question=question,
            expression=expression,
            result=result,
            variable=variable,
        )

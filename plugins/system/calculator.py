"""
Atlas Calculator Plugin

Safe mathematical expression evaluator for Atlas.
"""

import ast
import math
import operator
import re

from plugins.base import AtlasPlugin


# ==================================================
# SAFE OPERATORS
# ==================================================

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,

    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class CalculatorPlugin(AtlasPlugin):

    name = "calculator"

    display_name = "Calculator"

    description = (
        "Safely evaluates mathematical expressions."
    )

    icon = "🧮"

    has_gui = True

    gui_id = "calculator"

    priority = 20

    triggers = [
        "calculate",
        "calc",
        "solve",
        "compute",
        "evaluate",
        "what is",
        "what's",
    ]

    # ==================================================
    # CAN HANDLE
    # ==================================================

    def can_handle(
        self,
        message,
    ):
        text = str(
            message
        ).strip()

        if not text:
            return False

        lower = text.lower()

        # ----------------------------------------------
        # Explicit calculator commands
        # ----------------------------------------------

        for trigger in self.triggers:

            if lower == trigger:

                return True

            if lower.startswith(
                trigger + " "
            ):

                return True

        # ----------------------------------------------
        # Direct mathematical expression
        # ----------------------------------------------

        if self._looks_like_expression(
            text
        ):

            return True

        return False

    # ==================================================
    # EXPRESSION DETECTION
    # ==================================================

    def _looks_like_expression(
        self,
        text,
    ):
        """
        Detect raw mathematical expressions.

        Examples:

            25 * 4
            100 / 5
            2 ** 10
            (50 + 25) * 2
            10 % 3
        """

        text = text.strip()

        if not text:
            return False

        # Must contain a number.
        if not re.search(
            r"\d",
            text,
        ):
            return False

        # Only mathematical characters.
        if not re.fullmatch(
            r"[0-9eEpiPI+\-*/%().\s]+",
            text,
        ):
            return False

        # Must contain an operator.
        if not re.search(
            r"[+\-*/%]",
            text,
        ):
            return False

        return True

    # ==================================================
    # EXTRACT EXPRESSION
    # ==================================================

    def _extract_expression(
        self,
        message,
    ):
        """
        Extract the actual mathematical expression
        from a user message.
        """

        text = str(
            message
        ).strip()

        lower = text.lower()

        # ----------------------------------------------
        # Remove common trailing punctuation
        # ----------------------------------------------

        text = text.rstrip(
            "?!.,"
        ).strip()

        lower = text.lower()

        # ----------------------------------------------
        # Natural language prefixes
        # ----------------------------------------------

        prefixes = [
            "what is",
            "what's",
            "calculate",
            "calc",
            "compute",
            "evaluate",
            "solve",
        ]

        for prefix in prefixes:

            if lower == prefix:

                return ""

            if lower.startswith(
                prefix + " "
            ):

                expression = text[
                    len(prefix):
                ].strip()

                return expression

        # ----------------------------------------------
        # Raw expression
        # ----------------------------------------------

        return text

    # ==================================================
    # SAFE AST EVALUATION
    # ==================================================

    def _evaluate(
        self,
        node,
    ):

        # ----------------------------------------------
        # Numbers
        # ----------------------------------------------

        if isinstance(
            node,
            ast.Constant,
        ):

            if isinstance(
                node.value,
                (int, float),
            ):

                return node.value

            raise ValueError(
                "Invalid constant."
            )

        # ----------------------------------------------
        # Binary operations
        # ----------------------------------------------

        if isinstance(
            node,
            ast.BinOp,
        ):

            operation = _OPERATORS.get(
                type(node.op)
            )

            if operation is None:

                raise ValueError(
                    "Unsupported operator."
                )

            left = self._evaluate(
                node.left
            )

            right = self._evaluate(
                node.right
            )

            return operation(
                left,
                right,
            )

        # ----------------------------------------------
        # Unary operations
        # ----------------------------------------------

        if isinstance(
            node,
            ast.UnaryOp,
        ):

            operation = _OPERATORS.get(
                type(node.op)
            )

            if operation is None:

                raise ValueError(
                    "Unsupported operator."
                )

            return operation(
                self._evaluate(
                    node.operand
                )
            )

        # ----------------------------------------------
        # Mathematical constants
        # ----------------------------------------------

        if isinstance(
            node,
            ast.Name,
        ):

            constants = {
                "pi": math.pi,
                "e": math.e,
            }

            if node.id in constants:

                return constants[
                    node.id
                ]

        raise ValueError(
            "Unsupported expression."
        )

    # ==================================================
    # RUN
    # ==================================================

    def run(
        self,
        expression="",
        **kwargs,
    ):
        """
        Execute a mathematical expression.
        """

        try:

            expression = self._extract_expression(
                expression
            )

            expression = expression.strip()

            if not expression:

                return "Invalid expression."

            # ------------------------------------------
            # Validate expression characters
            # ------------------------------------------

            if not re.fullmatch(
                r"[0-9eEpiPI+\-*/%().\s]+",
                expression,
            ):

                return "Invalid expression."

            # ------------------------------------------
            # Parse safely
            # ------------------------------------------

            tree = ast.parse(
                expression,
                mode="eval",
            )

            result = self._evaluate(
                tree.body
            )

            return self._format_result(
                result
            )

        except ZeroDivisionError:

            return "Cannot divide by zero."

        except (
            ValueError,
            SyntaxError,
            TypeError,
            OverflowError,
        ):

            return "Invalid expression."

        except Exception:

            return "Invalid expression."

    # ==================================================
    # FORMAT RESULT
    # ==================================================

    def _format_result(
        self,
        result,
    ):

        if isinstance(
            result,
            float,
        ):

            if not math.isfinite(
                result
            ):

                return "Result is not finite."

            if result.is_integer():

                return str(
                    int(result)
                )

            return f"{result:.12g}"

        return str(
            result
        )
"""
Calculator Plugin
"""

import ast
import operator

from plugins.base import AtlasPlugin


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

    description = (
        "Safely evaluates mathematical expressions."
    )

    triggers = [
        "calculate",
        "calc",
        "solve",
    ]

    def can_handle(
        self,
        message,
    ):

        text = message.lower().strip()

        for trigger in self.triggers:

            if text == trigger:
                return True

            if text.startswith(
                trigger + " "
            ):
                return True

        return False

    def _evaluate(
        self,
        node,
    ):

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

            return operation(
                self._evaluate(
                    node.left
                ),
                self._evaluate(
                    node.right
                ),
            )

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

        raise ValueError(
            "Unsupported expression."
        )

    def run(
        self,
        expression="",
        **kwargs,
    ):

        try:

            tree = ast.parse(
                expression,
                mode="eval",
            )

            result = self._evaluate(
                tree.body
            )

            return str(result)

        except Exception:

            return "Invalid expression."
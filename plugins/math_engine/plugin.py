"""
Atlas Math Plugin

Connects AtlasPlugin to the deterministic MathEngine.
"""

from plugins.base import AtlasPlugin
from plugins.math_engine.engine import MathEngine


class MathPlugin(AtlasPlugin):

    name = "math"

    display_name = "Mathematics"

    description = (
        "Symbolic mathematics including "
        "differentiation, integration, algebra, "
        "simplification, factoring and equations."
    )

    icon = "∑"

    has_gui = False

    gui_id = "math"

    triggers = [
        "differentiate",
        "derivative",
        "differentiate",
        "integrate",
        "integral",
        "simplify",
        "factor",
        "expand",
        "solve",
    ]

    # ==================================================
    # Initialization
    # ==================================================

    def __init__(self):
        super().__init__()

        # One deterministic math engine for this plugin.
        self.engine = MathEngine()

    # ==================================================
    # Can Handle
    # ==================================================

    def can_handle(self, message):

        text = (
            str(message)
            .lower()
            .strip()
        )

        for trigger in self.triggers:

            if text == trigger:
                return True

            if text.startswith(
                trigger + " "
            ):
                return True

        return False

    # ==================================================
    # Run
    # ==================================================

    def run(
        self,
        expression="",
        operation="",
        variable="t",
        **kwargs,
    ):

        try:

            operation = (
                str(operation)
                .lower()
                .strip()
            )

            expression = (
                str(expression)
                .strip()
            )

            if not expression:

                raise ValueError(
                    "No mathematical expression provided."
                )

            # --------------------------------------------------
            # Differentiation
            # --------------------------------------------------

            if operation in (
                "differentiate",
                "derivative",
                "diff",
            ):

                result = self.engine.differentiate(
                    expression,
                    variable,
                )

                return self.engine.format(
                    result
                )

            # --------------------------------------------------
            # Integration
            # --------------------------------------------------

            if operation in (
                "integrate",
                "integral",
            ):

                result = self.engine.integrate(
                    expression,
                    variable,
                )

                return self.engine.format(
                    result
                )

            # --------------------------------------------------
            # Calculate
            # --------------------------------------------------

            if operation in (
                "calculate",
                "calc",
                "evaluate",
            ):

                result = self.engine.calculate(
                    expression
                )

                return self.engine.format(
                    result
                )

            # --------------------------------------------------
            # Simplify
            # --------------------------------------------------

            if operation == "simplify":

                result = self.engine.simplify(
                    expression
                )

                return self.engine.format(
                    result
                )

            # --------------------------------------------------
            # Expand
            # --------------------------------------------------

            if operation == "expand":

                result = self.engine.expand(
                    expression
                )

                return self.engine.format(
                    result
                )

            # --------------------------------------------------
            # Factor
            # --------------------------------------------------

            if operation in (
                "factor",
                "factorize",
                "factorise",
            ):

                result = self.engine.factor(
                    expression
                )

                return self.engine.format(
                    result
                )

            # --------------------------------------------------
            # Solve
            # --------------------------------------------------

            if operation == "solve":

                solve_method = getattr(
                    self.engine,
                    "solve",
                    None,
                )

                if solve_method is None:

                    raise ValueError(
                        "Solve operation is not implemented "
                        "in MathEngine yet."
                    )

                result = solve_method(
                    expression,
                    variable,
                )

                return self.engine.format(
                    result
                )

            raise ValueError(
                "Unsupported mathematical operation: "
                f"{operation}"
            )

        except Exception as error:

            return {
                "operation": operation,
                "expression": expression,
                "error": str(error),
            }
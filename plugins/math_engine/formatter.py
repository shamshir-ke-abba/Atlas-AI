"""
Atlas Math Formatter

Converts SymPy results into clean text/Markdown
for the Atlas GUI.
"""

import sympy as sp


class MathFormatter:

    # ======================================================
    # Basic
    # ======================================================

    @staticmethod
    def text(
        expression,
    ):

        if isinstance(
            expression,
            sp.Basic,
        ):

            return sp.sstr(
                expression
            )

        return str(
            expression
        )

    # ======================================================
    # Equation
    # ======================================================

    @staticmethod
    def equation(
        left,
        right,
    ):

        return (
            f"`{MathFormatter.text(left)}`"
            " = "
            f"**{MathFormatter.text(right)}**"
        )

    # ======================================================
    # Result Card
    # ======================================================

    @staticmethod
    def result(
        expression,
        result,
    ):

        return (
            "### Result\n\n"
            f"`{expression}` = **{result}**"
        )

    # ======================================================
    # Error
    # ======================================================

    @staticmethod
    def error(
        message,
    ):

        return (
            "### Math Error\n\n"
            f"{message}"
        )
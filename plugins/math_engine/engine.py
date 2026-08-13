"""
Atlas Math Engine

Fast local mathematics engine used by Atlas tools.

This module performs mathematical operations locally
instead of sending simple mathematical questions to
the LLM.

Supported:
- arithmetic
- differentiation
- integration
- simplification
- expansion
- factorization
"""

import re

import sympy as sp

from plugins.math_engine.formatter import MathFormatter


class MathEngine:

    def __init__(self):
        self.symbols = {}

    # ==================================================
    # Expression Parser
    # ==================================================

    def parse_expression(self, expression):
        """
        Convert a text expression into a SymPy expression.
        """

        expression = expression.strip()

        if not expression:
            raise ValueError("Expression is empty.")

        # Common mathematical notation
        expression = expression.replace("^", "**")

        # Create common symbols automatically
        symbols = {
            name: sp.Symbol(name)
            for name in [
                "x",
                "y",
                "z",
                "t",
                "a",
                "b",
                "c",
                "n",
            ]
        }

        return sp.sympify(
            expression,
            locals=symbols,
        )

    # ==================================================
    # Arithmetic
    # ==================================================

    def calculate(self, expression):
        """
        Evaluate/simplify an arithmetic expression.
        """

        parsed = self.parse_expression(
            expression
        )

        return sp.simplify(parsed)

    # ==================================================
    # Differentiation
    # ==================================================

    def differentiate(
        self,
        expression,
        variable="x",
    ):
        """
        Differentiate an expression with respect
        to the specified variable.
        """

        parsed = self.parse_expression(
            expression
        )

        symbol = sp.Symbol(variable)

        return sp.diff(
            parsed,
            symbol,
        )

    # ==================================================
    # Integration
    # ==================================================

    def integrate(
        self,
        expression,
        variable="x",
    ):
        """
        Integrate an expression with respect
        to the specified variable.
        """

        parsed = self.parse_expression(
            expression
        )

        symbol = sp.Symbol(variable)

        return sp.integrate(
            parsed,
            symbol,
        )

    # ==================================================
    # Simplification
    # ==================================================

    def simplify(self, expression):
        """
        Simplify a mathematical expression.
        """

        parsed = self.parse_expression(
            expression
        )

        return sp.simplify(
            parsed
        )

    # ==================================================
    # Expansion
    # ==================================================

    def expand(self, expression):
        """
        Expand an expression.
        """

        parsed = self.parse_expression(
            expression
        )

        return sp.expand(
            parsed
        )

    # ==================================================
    # Factorization
    # ==================================================

    def factor(self, expression):
        """
        Factor an expression.
        """

        parsed = self.parse_expression(
            expression
        )

        return sp.factor(
            parsed
        )

    # ==================================================
    # Generic Operation
    # ==================================================

    def execute(
        self,
        operation,
        expression,
        variable="x",
    ):
        """
        Execute a mathematical operation.
        """

        operation = operation.lower().strip()

        if operation in (
            "calculate",
            "calc",
            "evaluate",
            "evaluate_expression",
        ):
            return self.calculate(
                expression
            )

        if operation in (
            "differentiate",
            "derivative",
            "diff",
        ):
            return self.differentiate(
                expression,
                variable,
            )

        if operation in (
            "integrate",
            "integral",
        ):
            return self.integrate(
                expression,
                variable,
            )

        if operation in (
            "simplify",
        ):
            return self.simplify(
                expression
            )

        if operation in (
            "expand",
        ):
            return self.expand(
                expression
            )

        if operation in (
            "factor",
            "factorize",
            "factorise",
        ):
            return self.factor(
                expression
            )

        raise ValueError(
            f"Unsupported mathematical operation: "
            f"{operation}"
        )

    # ==================================================
    # Formatting
    # ==================================================

    def format(
        self,
        expression,
    ):
        """
        Convert a SymPy result into display text.
        """

        return MathFormatter.text(
            expression
        )

    # ==================================================
    # Expression Extraction
    # ==================================================

    def extract_expression(
        self,
        text,
        fallback="",
    ):
        """
        Extract a mathematical expression from
        natural language text.
        """

        text = text.strip()

        if not text:
            return fallback

        lower = text.lower()

        triggers = [
            "calculate",
            "calc",
            "solve",
            "evaluate",
            "what is",
            "compute",
        ]

        for trigger in triggers:

            if lower.startswith(
                trigger + " "
            ):

                candidate = (
                    text[
                        len(trigger):
                    ]
                    .strip()
                    .rstrip("?.!")
                )

                if candidate:
                    return candidate

        match = re.search(
            r"[\d\.]+(?:\s*[\+\-\*/\^]\s*[\d\.x]+)+",
            text,
        )

        if match:

            return match.group(
                0
            ).strip()

        return fallback

    # ==================================================
    # Explanation
    # ==================================================

    def explain(
        self,
        question,
        expression="",
        result="",
    ):
        """
        Produce a deterministic explanation for
        a calculation without using the LLM.
        """

        question = question.strip()

        if not expression:

            expression = (
                self.extract_expression(
                    question
                )
            )

        if not expression:

            return MathFormatter.error(
                "No expression to explain."
            )

        if not result:

            try:

                calculated = self.calculate(
                    expression
                )

                result = self.format(
                    calculated
                )

            except Exception as error:

                return MathFormatter.error(
                    str(error)
                )

        lower = question.lower()

        wants_steps = any(
            word in lower
            for word in (
                "step",
                "how",
                "explain",
                "why",
                "show",
            )
        )

        lines = [
            "### Atlas Math",
            "",
            f"**Expression**\n\n`{expression}`",
            "",
            f"**Answer**\n\n**{result}**",
        ]

        if wants_steps:

            lines.extend(
                [
                    "",
                    "**Steps**",
                    "",
                    f"1. Read the expression `{expression}`.",
                    "2. Evaluate it with symbolic math.",
                    f"3. The result is **{result}**.",
                ]
            )

        else:

            lines.extend(
                [
                    "",
                    f"The value of `{expression}` is **{result}**.",
                ]
            )

        return "\n".join(
            lines
        )
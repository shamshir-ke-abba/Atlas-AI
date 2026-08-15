"""
Atlas V3 deterministic math engine.

Rejects arbitrary prose before SymPy parsing, supports implicit
multiplication, differentiation, integration, simplification, expansion,
factorization and equation solving.
"""

import re
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


class MathEngine:
    DEFAULT_VARIABLE = "x"
    SYMBOL_NAMES = ("x", "y", "z", "t", "a", "b", "c", "n")

    TRANSFORMATIONS = (
        standard_transformations
        + (convert_xor, implicit_multiplication_application)
    )

    FUNCTIONS = {
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "cot": sp.cot,
        "sec": sp.sec,
        "csc": sp.csc,
        "asin": sp.asin,
        "acos": sp.acos,
        "atan": sp.atan,
        "sqrt": sp.sqrt,
        "log": sp.log,
        "ln": sp.log,
        "exp": sp.exp,
        "abs": sp.Abs,
        "pi": sp.pi,
        "E": sp.E,
    }

    def __init__(self):
        self.symbols = {
            name: sp.Symbol(name)
            for name in self.SYMBOL_NAMES
        }

    def detect_operation(self, text):
        low = str(text or "").lower()

        if re.search(r"\b(?:differentiat(?:e|ion)|diffrentiat(?:e|ion))\b", low):
            return "differentiate"
        if re.search(r"\bderivative\b", low):
            return "differentiate"
        if re.search(r"\bintegr(?:ate|al)\b", low):
            return "integrate"
        if re.search(r"\bsimplify\b", low):
            return "simplify"
        if re.search(r"\bexpand\b", low):
            return "expand"
        if re.search(r"\bfactor(?:ize|ise|ization)?\b", low):
            return "factor"
        if re.search(r"\bsolve\b|\bequation\b|\broots?\b", low):
            return "solve"
        if re.search(
            r"\bcalculate\b|\bcalc\b|\bcompute\b|\bevaluate\b",
            low,
        ):
            return "calculate"

        # Plain numeric arithmetic belongs to CalculatorPlugin.
        # MathPlugin should only claim symbolic/named operations.
        return None

    def extract_expression(
        self,
        text,
        operation=None,
        fallback="",
    ):
        text = str(text or "").strip().rstrip("?!.,;")
        if not text:
            return fallback

        op = operation or self.detect_operation(text)
        if op is None:
            return ""

        patterns = [
            r"^\s*what\s+is\s+the\s+derivative\s+of\s+",
            r"^\s*find\s+the\s+derivative\s+of\s+",
            r"^\s*what\s+is\s+the\s+integral\s+of\s+",
            r"^\s*find\s+the\s+integral\s+of\s+",
            r"^\s*derivative\s+of\s+",
            r"^\s*integral\s+of\s+",
            r"^\s*diffrentiate\s+",
            r"^\s*diffrentiation\s+of\s+",
            r"^\s*differentiate\s+",
            r"^\s*integrate\s+",
            r"^\s*calculate\s+",
            r"^\s*calc\s+",
            r"^\s*compute\s+",
            r"^\s*evaluate\s+",
            r"^\s*simplify\s+",
            r"^\s*expand\s+",
            r"^\s*factor(?:ize|ise)?\s+",
            r"^\s*solve\s+",
        ]

        result = text
        for pattern in patterns:
            cleaned = re.sub(
                pattern,
                "",
                result,
                flags=re.IGNORECASE,
            )
            if cleaned != result:
                result = cleaned.strip()
                break

        if op == "calculate":
            result = re.sub(
                r"^\s*what(?:'s|\s+is)\s+",
                "",
                result,
                flags=re.IGNORECASE,
            ).strip()

        result = re.sub(
            r"\s+(?:with\s+respect\s+to|respect\s+to|wrt)\s+[A-Za-z_]\w*$",
            "",
            result,
            flags=re.IGNORECASE,
        ).strip()

        return result

    def _validate_expression(self, expression):
        expr = str(expression or "").strip()

        if not expr:
            raise ValueError(
                "No mathematical expression was provided."
            )

        if len(expr) > 500:
            raise ValueError("Expression is too long.")

        if not re.fullmatch(
            r"[0-9A-Za-z_+\-*/%^().,\s]+",
            expr,
        ):
            raise ValueError(
                "Invalid mathematical characters."
            )

        identifiers = re.findall(
            r"[A-Za-z_]\w*",
            expr,
        )
        allowed = set(self.SYMBOL_NAMES) | set(self.FUNCTIONS)

        for name in identifiers:
            if name not in allowed:
                raise ValueError(
                    f"'{name}' is not a recognized mathematical "
                    "symbol or function."
                )

        if not re.search(
            r"\d|[xyztabcn]\b",
            expr,
        ):
            raise ValueError(
                "Please provide a mathematical expression."
            )

        return (
            expr
            .replace("−", "-")
            .replace("×", "*")
            .replace("÷", "/")
        )

    def parse_expression(self, expression):
        expr = self._validate_expression(expression)

        local_dict = dict(self.symbols)
        local_dict.update(self.FUNCTIONS)

        return parse_expr(
            expr,
            local_dict=local_dict,
            transformations=self.TRANSFORMATIONS,
            evaluate=True,
        )

    def calculate(self, expression):
        return sp.simplify(
            self.parse_expression(expression)
        )

    def differentiate(self, expression, variable="x"):
        parsed = self.parse_expression(expression)
        variable = str(variable or "x").strip()
        symbol = self.symbols.get(
            variable,
            sp.Symbol(variable),
        )
        return sp.simplify(
            sp.diff(parsed, symbol)
        )

    def integrate(self, expression, variable="x"):
        parsed = self.parse_expression(expression)
        variable = str(variable or "x").strip()
        symbol = self.symbols.get(
            variable,
            sp.Symbol(variable),
        )
        return sp.integrate(parsed, symbol)

    def simplify(self, expression):
        return sp.simplify(
            self.parse_expression(expression)
        )

    def expand(self, expression):
        return sp.expand(
            self.parse_expression(expression)
        )

    def factor(self, expression):
        return sp.factor(
            self.parse_expression(expression)
        )

    def solve(self, equation, variable="x"):
        equation = str(equation or "").strip()
        if not equation:
            raise ValueError("Equation is empty.")

        variable = str(variable or "x").strip()
        symbol = self.symbols.get(
            variable,
            sp.Symbol(variable),
        )

        if "=" in equation:
            left, right = equation.split("=", 1)
            return sp.solve(
                sp.Eq(
                    self.parse_expression(left),
                    self.parse_expression(right),
                ),
                symbol,
            )

        return sp.solve(
            self.parse_expression(equation),
            symbol,
        )

    def execute(self, operation, expression, variable="x"):
        operation = str(operation or "").lower().strip()

        aliases = {
            "calc": "calculate",
            "evaluate": "calculate",
            "derivative": "differentiate",
            "diff": "differentiate",
            "integral": "integrate",
            "factorize": "factor",
            "factorise": "factor",
            "equation": "solve",
            "equations": "solve",
        }
        operation = aliases.get(operation, operation)

        if operation == "calculate":
            return self.calculate(expression)
        if operation == "differentiate":
            return self.differentiate(expression, variable)
        if operation == "integrate":
            return self.integrate(expression, variable)
        if operation == "simplify":
            return self.simplify(expression)
        if operation == "expand":
            return self.expand(expression)
        if operation == "factor":
            return self.factor(expression)
        if operation == "solve":
            return self.solve(expression, variable)

        raise ValueError(
            "Unsupported mathematical operation."
        )

    def format(self, expression):
        return self._pretty(expression)

    @staticmethod
    def _pretty(expression):
        if isinstance(expression, (list, tuple)):
            return ", ".join(
                MathEngine._pretty(item)
                for item in expression
            )

        if isinstance(expression, sp.Equality):
            return (
                MathEngine._pretty(expression.lhs)
                + " = "
                + MathEngine._pretty(expression.rhs)
            )

        text = sp.sstr(expression)

        superscripts = str.maketrans(
            "0123456789+-=()",
            "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾",
        )

        def power_replace(match):
            base = match.group(1)
            power = match.group(2)

            if len(power) <= 3 and re.fullmatch(
                r"[0-9+\-()]+",
                power,
            ):
                return base + power.translate(superscripts)

            return f"{base}^{power}"

        text = re.sub(
            r"([A-Za-z0-9.)]+)\*\*([0-9+\-()]+)",
            power_replace,
            text,
        )
        text = text.replace("*", "·")
        text = text.replace("/", "⁄")

        return text

    def explain(
        self,
        question,
        expression="",
        result="",
        variable="x",
    ):
        question = str(question or "").strip()
        operation = self.detect_operation(question)

        if operation is None:
            return (
                "### Math Error\n\n"
                "I need a specific mathematical operation, such as "
                "differentiate, integrate, simplify, solve or calculate."
            )

        expression = str(expression or "").strip()
        if not expression:
            expression = self.extract_expression(
                question,
                operation,
            )

        if not expression:
            return (
                "### Math Error\n\n"
                "Please provide the mathematical expression to work on."
            )

        try:
            if not result:
                result = self.execute(
                    operation,
                    expression,
                    variable,
                )

            formatted = self.format(result)

        except Exception as exc:
            return f"### Math Error\n\n{exc}"

        lines = [
            "### Atlas Math",
            "",
            "**Expression**",
            "",
            f"`{expression}`",
            "",
            "**Answer**",
            "",
            formatted,
        ]

        if operation == "differentiate":
            lines += [
                "",
                "**Steps**",
                "",
                f"1. Treat `{variable}` as the differentiation variable.",
                "2. Differentiate each term.",
                f"3. Simplify the result: **{formatted}**.",
            ]
        elif operation == "integrate":
            lines += [
                "",
                "**Steps**",
                "",
                f"1. Treat `{variable}` as the integration variable.",
                "2. Integrate each term.",
                f"3. Add the constant of integration: **{formatted} + C**.",
            ]
        else:
            lines += [
                "",
                "**Steps**",
                "",
                "1. Parse the expression symbolically.",
                f"2. Apply **{operation}**.",
                f"3. Simplify the result: **{formatted}**.",
            ]

        return "\n".join(lines)

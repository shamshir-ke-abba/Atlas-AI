"""Atlas calculator: exact arithmetic with fractions."""

import ast
import math
import operator
import re
from fractions import Fraction
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
    display_name = "Calculator"
    description = "Exact numeric arithmetic, including fractions."
    icon = "🧮"
    has_gui = True
    gui_id = "calculator"
    priority = 10
    triggers = ["calculate", "calc", "compute", "evaluate", "what is", "what's"]

    def can_handle(self, message):
        text = str(message or "").strip()
        if not text:
            return False
        low = text.lower()
        if any(low == t or low.startswith(t + " ") for t in self.triggers):
            expr = self._extract_expression(text)
            return bool(expr) and self._is_numeric_expression(expr)
        return self._is_numeric_expression(text)

    def _extract_expression(self, message):
        text = str(message or "").strip().rstrip("?!.,")
        low = text.lower()
        for prefix in ("what is", "what's", "calculate", "calc", "compute", "evaluate"):
            if low == prefix:
                return ""
            if low.startswith(prefix + " "):
                return text[len(prefix):].strip()
        return text

    @staticmethod
    def _normalize(text):
        return (str(text or "")
                .replace("÷", "/")
                .replace("×", "*")
                .replace("−", "-")
                .replace("–", "-")
                .replace("—", "-")
                .replace("π", "pi"))

    def _is_numeric_expression(self, text):
        text = self._normalize(text).strip()
        if not text or not re.search(r"\d", text):
            return False
        if not re.fullmatch(r"[0-9eEpiPI+\-*/%^().\s]+", text):
            return False
        return bool(re.search(r"[+\-*/%^]", text))

    def _evaluate(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int):
                return Fraction(node.value, 1)
            if isinstance(node.value, float):
                return Fraction(str(node.value))
            raise ValueError("Invalid constant.")
        if isinstance(node, ast.BinOp):
            op = _OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError("Unsupported operator.")
            return op(self._evaluate(node.left), self._evaluate(node.right))
        if isinstance(node, ast.UnaryOp):
            op = _OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError("Unsupported operator.")
            return op(self._evaluate(node.operand))
        if isinstance(node, ast.Name) and node.id.lower() in ("pi", "e"):
            return math.pi if node.id.lower() == "pi" else math.e
        raise ValueError("Unsupported expression.")

    def run(self, expression="", **kwargs):
        try:
            expression = self._normalize(self._extract_expression(expression))
            if not self._is_numeric_expression(expression):
                return "Invalid expression."
            expression = expression.replace("^", "**")
            tree = ast.parse(expression, mode="eval")
            return self._format_result(self._evaluate(tree.body))
        except ZeroDivisionError:
            return "Cannot divide by zero."
        except (ValueError, SyntaxError, TypeError, OverflowError):
            return "Invalid expression."
        except Exception:
            return "Invalid expression."

    @staticmethod
    def _format_result(result):
        if isinstance(result, Fraction):
            return str(result.numerator) if result.denominator == 1 else f"{result.numerator}/{result.denominator}"
        if isinstance(result, float):
            if not math.isfinite(result):
                return "Result is not finite."
            return str(int(result)) if result.is_integer() else f"{result:.12g}"
        return str(result)

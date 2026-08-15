"""
Atlas Math Formatter compatibility layer.
"""


class MathFormatter:
    @staticmethod
    def text(expression):
        from plugins.math_engine.engine import MathEngine
        return MathEngine._pretty(expression)

    @staticmethod
    def equation(left, right):
        from plugins.math_engine.engine import MathEngine
        return (
            f"{MathEngine._pretty(left)} = "
            f"{MathEngine._pretty(right)}"
        )

    @staticmethod
    def result(expression, result):
        from plugins.math_engine.engine import MathEngine
        return (
            "### Result\n\n"
            f"`{expression}` = {MathEngine._pretty(result)}"
        )

    @staticmethod
    def error(message):
        return f"### Math Error\n\n{message}"

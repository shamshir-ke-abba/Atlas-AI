"""
Regression tests for Atlas V3 GUI/math fixes.
"""

from core.conversation import ConversationManager
from plugins.math_engine.engine import MathEngine


def test_integrate_natural_language_expression():
    math = MathEngine()
    expression = math.extract_expression("integrate 2x**2 + 4")
    assert expression == "2x**2 + 4"

    result = math.integrate(expression, "x")
    assert str(result) == "2*x**3/3 + 4*x"


def test_integrate_with_caret_notation():
    math = MathEngine()
    result = math.integrate("2x^2 + 4", "x")
    assert str(result) == "2*x**3/3 + 4*x"


def test_conversation_manager_has_messages():
    conversation = ConversationManager(
        "test-id",
        "Test",
    )
    conversation.add_message(
        "User",
        "Hello",
        True,
    )
    assert conversation.get_messages()[0]["text"] == "Hello"


def test_math_power_format_is_visual():
    math = MathEngine()
    result = math.calculate("x**2 + 4")
    formatted = math.format(result)
    assert "x²" in formatted

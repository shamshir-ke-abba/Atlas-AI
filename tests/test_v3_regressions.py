from plugins.math_engine.plugin import MathPlugin
from plugins.system.calculator import CalculatorPlugin
from plugins.system.web_search import WebSearchPlugin


def test_math_integration():
    p = MathPlugin()
    result = p.run("integrate 2x**2 + 4")
    assert "x" in result
    assert "3" in result


def test_math_differentiation():
    p = MathPlugin()
    result = p.run("differentiate 2x**2 + 4")
    assert "4" in result
    assert "x" in result


def test_math_typo_differentiation():
    p = MathPlugin()
    result = p.run("Diffrentiate 2x^2 + 4")
    assert "4" in result
    assert "x" in result


def test_math_rejects_prose():
    p = MathPlugin()
    assert not p.can_handle("hahha")
    assert not p.can_handle("Explain why")


def test_calculator_owns_numeric_question():
    c = CalculatorPlugin()
    assert c.can_handle("What is 2 + 2")
    assert c.run("What is 2 + 2") == "4"


def test_web_context_format():
    plugin = WebSearchPlugin()
    text = plugin._format_results(
        "When is India's Independence day?",
        [{
            "title": "Example source",
            "url": "https://example.com",
            "snippet": "India's Independence Day is observed on 15 August.",
        }],
    )
    assert "You asked:" in text
    assert "Example source" in text

import pytest

from agents.coding.error_analyzer import (
    CodingErrorAnalyzer,
    ErrorAnalysis,
)


def test_successful_result():
    analyzer = CodingErrorAnalyzer()

    result = analyzer.analyze({
        "success": True,
        "stdout": "59 passed",
        "stderr": "",
    })

    assert isinstance(result, ErrorAnalysis)
    assert result.success is True
    assert result.message == "Tests passed."


def test_assertion_error():
    analyzer = CodingErrorAnalyzer()

    result = analyzer.analyze({
        "success": False,
        "stdout": (
            'File "app.py", line 42, in test_value\n'
            "    assert value == 10\n"
            "AssertionError: assert 5 == 10\n"
        ),
        "stderr": "",
    })

    assert result.success is False
    assert result.error_type == "assertion_error"
    assert "app.py" in result.files
    assert 42 in result.lines
    assert result.suggestions


def test_syntax_error():
    analyzer = CodingErrorAnalyzer()

    result = analyzer.analyze({
        "success": False,
        "stdout": (
            'File "broken.py", line 7\n'
            "    def broken(\n"
            "SyntaxError: '(' was never closed\n"
        ),
        "stderr": "",
    })

    assert result.error_type == "syntax_error"
    assert "broken.py" in result.files
    assert 7 in result.lines


def test_type_error():
    analyzer = CodingErrorAnalyzer()

    result = analyzer.analyze({
        "success": False,
        "stdout": (
            'File "calculator.py", line 15\n'
            "TypeError: unsupported operation\n"
        ),
        "stderr": "",
    })

    assert result.error_type == "type_error"
    assert "calculator.py" in result.files
    assert 15 in result.lines


def test_module_not_found():
    analyzer = CodingErrorAnalyzer()

    result = analyzer.analyze({
        "success": False,
        "stdout": (
            'File "app.py", line 3\n'
            "ModuleNotFoundError: No module named 'missing'\n"
        ),
        "stderr": "",
    })

    assert result.error_type == "module_not_found"
    assert result.files == ["app.py"]
    assert result.lines == [3]


def test_multiple_traceback_locations():
    analyzer = CodingErrorAnalyzer()

    result = analyzer.analyze({
        "success": False,
        "stdout": (
            'File "test_app.py", line 10\n'
            "    run_app()\n"
            'File "app.py", line 25\n'
            "    return broken()\n"
            "NameError: name 'broken' is not defined\n"
        ),
        "stderr": "",
    })

    assert result.error_type == "name_error"
    assert "test_app.py" in result.files
    assert "app.py" in result.files
    assert 10 in result.lines
    assert 25 in result.lines


def test_unknown_failure():
    analyzer = CodingErrorAnalyzer()

    result = analyzer.analyze({
        "success": False,
        "stdout": "FAILED tests/test_app.py",
        "stderr": "",
    })

    assert result.success is False
    assert result.error_type == "test_failure"
    assert result.message


def test_invalid_result():
    analyzer = CodingErrorAnalyzer()

    result = analyzer.analyze(None)

    assert result.success is False
    assert result.error_type == "invalid_result"


def test_empty_failure_output():
    analyzer = CodingErrorAnalyzer()

    result = analyzer.analyze({
        "success": False,
        "stdout": "",
        "stderr": "",
    })

    assert result.success is False
    assert result.error_type == "test_failure"
    assert result.message
    assert result.suggestions
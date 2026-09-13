from agents.coding.detector import CodingTaskDetector


def test_detects_explicit_bug_fix():
    detector = CodingTaskDetector()

    assert detector.is_coding_task(
        "Fix the bug in agents/coding/context.py"
    )


def test_detects_debugging_request():
    detector = CodingTaskDetector()

    assert detector.is_coding_task(
        "Debug the pytest failure"
    )


def test_detects_repository_inspection():
    detector = CodingTaskDetector()

    assert detector.is_coding_task(
        "Inspect this repository and find the problem"
    )


def test_detects_code_change():
    detector = CodingTaskDetector()

    assert detector.is_coding_task(
        "Add a new test for the coding agent"
    )


def test_detects_python_error_question():
    detector = CodingTaskDetector()

    assert detector.is_coding_task(
        "Why is this Python function throwing an exception?"
    )


def test_rejects_general_programming_question():
    detector = CodingTaskDetector()

    assert not detector.is_coding_task(
        "What is Python?"
    )


def test_rejects_study_request():
    detector = CodingTaskDetector()

    assert not detector.is_coding_task(
        "Explain Python functions for my exam"
    )


def test_rejects_normal_conversation():
    detector = CodingTaskDetector()

    assert not detector.is_coding_task(
        "Tell me a joke about computers"
    )


def test_empty_message_is_not_coding():
    detector = CodingTaskDetector()

    assert not detector.is_coding_task("")
    assert not detector.is_coding_task(None)

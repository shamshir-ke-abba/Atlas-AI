from agents.coding.change_generator import (
    CodeChange,
    ChangeSet,
    CodingChangeGenerator,
)


class FakeModel:
    def __init__(self, response):
        self.response = response

    def generate(self, prompt):
        return self.response


def test_empty_task_returns_empty_changes():
    generator = CodingChangeGenerator(
        model=FakeModel("CHANGE:")
    )

    result = generator.generate(
        "",
        None,
        "",
    )

    assert isinstance(result, ChangeSet)
    assert result.changes == []


def test_no_model_returns_empty_changes():
    generator = CodingChangeGenerator()

    result = generator.generate(
        "Fix the bug",
        None,
        "example.py",
    )

    assert isinstance(result, ChangeSet)
    assert result.changes == []


def test_parse_single_change():
    response = """CHANGE:
PATH:
agents/example.py
OLD_TEXT:
VALUE = 1
NEW_TEXT:
VALUE = 2
REASON:
Fix the incorrect value.
"""

    result = CodingChangeGenerator._parse_response(
        response
    )

    assert len(result.changes) == 1

    change = result.changes[0]

    assert isinstance(change, CodeChange)
    assert change.path == "agents/example.py"
    assert change.old_text == "VALUE = 1"
    assert change.new_text == "VALUE = 2"
    assert change.reason == "Fix the incorrect value."


def test_parse_multiple_changes():
    response = """CHANGE:
PATH:
first.py
OLD_TEXT:
A = 1
NEW_TEXT:
A = 2
REASON:
Update A.

CHANGE:
PATH:
second.py
OLD_TEXT:
B = 3
NEW_TEXT:
B = 4
REASON:
Update B.
"""

    result = CodingChangeGenerator._parse_response(
        response
    )

    assert len(result.changes) == 2

    assert result.changes[0].path == "first.py"
    assert result.changes[1].path == "second.py"


def test_invalid_change_without_path_is_ignored():
    response = """CHANGE:
OLD_TEXT:
VALUE = 1
NEW_TEXT:
VALUE = 2
REASON:
Missing path.
"""

    result = CodingChangeGenerator._parse_response(
        response
    )

    assert result.changes == []


def test_invalid_change_without_old_text_is_ignored():
    response = """CHANGE:
PATH:
example.py
NEW_TEXT:
VALUE = 2
REASON:
Missing old text.
"""

    result = CodingChangeGenerator._parse_response(
        response
    )

    assert result.changes == []


def test_model_generates_change_set():
    response = """CHANGE:
PATH:
example.py
OLD_TEXT:
VALUE = 1
NEW_TEXT:
VALUE = 2
REASON:
Correct the value.
"""

    generator = CodingChangeGenerator(
        model=FakeModel(response)
    )

    result = generator.generate(
        "Fix example.py",
        type(
            "Plan",
            (),
            {
                "objective": "Fix example",
                "files_to_inspect": ["example.py"],
                "changes": ["Change VALUE"],
                "tests": ["Run pytest"],
                "risks": [],
            },
        )(),
        "example.py\nVALUE = 1",
    )

    assert len(result.changes) == 1
    assert result.changes[0].path == "example.py"


def test_multiline_change_is_preserved():
    response = """CHANGE:
PATH:
example.py
OLD_TEXT:
def hello():
    return "old"
NEW_TEXT:
def hello():
    return "new"
REASON:
Update the return value.
"""

    result = CodingChangeGenerator._parse_response(
        response
    )

    assert len(result.changes) == 1

    change = result.changes[0]

    assert change.old_text == (
        'def hello():\n'
        '    return "old"'
    )

    assert change.new_text == (
        'def hello():\n'
        '    return "new"'
    )


def test_format_items():
    result = CodingChangeGenerator._format_items(
        ["one", "two"]
    )

    assert result == "- one\n- two"


def test_format_empty_items():
    result = CodingChangeGenerator._format_items(
        []
    )

    assert result == "- None identified."
import pytest

from agents.coding.permissions import CodingPermissions
from agents.coding.editor import CodingEditor
from agents.coding.test_runner import CodingTestRunner


def test_write_is_denied_by_default(tmp_path):
    target = tmp_path / "example.py"
    target.write_text("print('old')")

    editor = CodingEditor(
        tmp_path,
        permissions=CodingPermissions(),
    )

    with pytest.raises(PermissionError):
        editor.write_file(
            target,
            "print('new')",
        )

    assert target.read_text() == "print('old')"


def test_tests_are_denied_by_default(tmp_path):
    test_dir = tmp_path / "tests"
    test_dir.mkdir()

    runner = CodingTestRunner(
        tmp_path,
        permissions=CodingPermissions(),
    )

    with pytest.raises(PermissionError):
        runner.run("tests")


def test_write_permission_allows_modification(tmp_path):
    target = tmp_path / "example.py"
    target.write_text("print('old')")

    permissions = CodingPermissions(
        allow_write=True,
    )

    editor = CodingEditor(
        tmp_path,
        permissions=permissions,
    )

    result = editor.write_file(
        target,
        "print('new')",
    )

    assert result["success"] is True
    assert target.read_text() == "print('new')"


def test_test_permission_allows_pytest(tmp_path):
    test_dir = tmp_path / "tests"
    test_dir.mkdir()

    test_file = test_dir / "test_example.py"
    test_file.write_text(
        "def test_example():\n"
        "    assert 1 + 1 == 2\n"
    )

    permissions = CodingPermissions(
        allow_tests=True,
    )

    runner = CodingTestRunner(
        tmp_path,
        permissions=permissions,
    )

    result = runner.run("tests")

    assert result["success"] is True
    assert result["returncode"] == 0


def test_git_permission_is_disabled_by_default():
    permissions = CodingPermissions()

    assert permissions.allow_git is False

    with pytest.raises(PermissionError):
        permissions.check_git()


def test_path_escape_is_rejected_even_with_write_permission(tmp_path):
    permissions = CodingPermissions(
        allow_write=True,
    )

    editor = CodingEditor(
        tmp_path,
        permissions=permissions,
    )

    outside = tmp_path.parent / "outside.py"

    with pytest.raises(PermissionError):
        editor.write_file(
            outside,
            "should not be written",
        )

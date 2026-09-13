import pytest

from agents.coding.permissions import CodingPermissions
from agents.coding.test_runner import CodingTestRunner


def make_runner(tmp_path, allow_tests=False):
    permissions = CodingPermissions(
        allow_tests=allow_tests
    )

    return CodingTestRunner(
        tmp_path,
        permissions=permissions,
    )


def test_tests_require_permission(tmp_path):
    (tmp_path / "tests").mkdir()

    runner = make_runner(tmp_path)

    with pytest.raises(PermissionError):
        runner.run()


def test_missing_test_path_is_rejected(tmp_path):
    runner = make_runner(
        tmp_path,
        allow_tests=True,
    )

    with pytest.raises(FileNotFoundError):
        runner.run("tests")


def test_successful_test_run(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    test_file = tests_dir / "test_example.py"

    test_file.write_text(
        "def test_example():\n"
        "    assert 1 + 1 == 2\n",
        encoding="utf-8",
    )

    runner = make_runner(
        tmp_path,
        allow_tests=True,
    )

    result = runner.run()

    assert result["success"] is True
    assert result["returncode"] == 0
    assert result["timeout"] is False
    assert result["summary"] == "Tests passed."


def test_failed_test_run(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    test_file = tests_dir / "test_example.py"

    test_file.write_text(
        "def test_example():\n"
        "    assert 1 == 2\n",
        encoding="utf-8",
    )

    runner = make_runner(
        tmp_path,
        allow_tests=True,
    )

    result = runner.run()

    assert result["success"] is False
    assert result["returncode"] != 0
    assert result["timeout"] is False
    assert result["summary"] == "Tests failed."
    assert result["output"]


def test_test_path_cannot_escape_root(tmp_path):
    runner = make_runner(
        tmp_path,
        allow_tests=True,
    )

    with pytest.raises(PermissionError):
        runner.run("../")


def test_specific_test_file(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    test_file = tests_dir / "test_specific.py"

    test_file.write_text(
        "def test_specific():\n"
        "    assert True\n",
        encoding="utf-8",
    )

    runner = make_runner(
        tmp_path,
        allow_tests=True,
    )

    result = runner.run(
        "tests/test_specific.py"
    )

    assert result["success"] is True
    assert result["returncode"] == 0
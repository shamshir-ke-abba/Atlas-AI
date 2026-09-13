from dataclasses import dataclass
from pathlib import Path

import pytest

from agents.coding.executor import CodingExecutor
from agents.coding.permissions import CodingPermissions


@dataclass
class FakeChange:
    path: str
    old_text: str
    new_text: str
    reason: str = ""


def make_executor(tmp_path, allow_write=False):
    permissions = CodingPermissions(
        allow_read=True,
        allow_search=True,
        allow_list=True,
        allow_write=allow_write,
        allow_tests=False,
        allow_git=False,
    )

    return CodingExecutor(
        tmp_path,
        permissions=permissions,
    )


def test_apply_change_requires_write_permission(tmp_path):
    target = Path(tmp_path) / "example.py"
    target.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    executor = make_executor(
        tmp_path,
        allow_write=False,
    )

    change = FakeChange(
        path="example.py",
        old_text="value = 1",
        new_text="value = 2",
    )

    with pytest.raises(PermissionError):
        executor.apply_change(change)

    assert target.read_text(
        encoding="utf-8"
    ) == "value = 1\n"


def test_apply_change_modifies_file(tmp_path):
    target = Path(tmp_path) / "example.py"
    target.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    executor = make_executor(
        tmp_path,
        allow_write=True,
    )

    change = FakeChange(
        path="example.py",
        old_text="value = 1",
        new_text="value = 2",
    )

    result = executor.apply_change(change)

    assert result["success"] is True
    assert result["path"] == "example.py"

    assert target.read_text(
        encoding="utf-8"
    ) == "value = 2\n"


def test_apply_change_rejects_none(tmp_path):
    executor = make_executor(
        tmp_path,
        allow_write=True,
    )

    with pytest.raises(ValueError):
        executor.apply_change(None)


def test_apply_change_rejects_missing_file(tmp_path):
    executor = make_executor(
        tmp_path,
        allow_write=True,
    )

    change = FakeChange(
        path="missing.py",
        old_text="value = 1",
        new_text="value = 2",
    )

    with pytest.raises(FileNotFoundError):
        executor.apply_change(change)


def test_apply_change_rejects_missing_old_text(tmp_path):
    target = Path(tmp_path) / "example.py"
    target.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    executor = make_executor(
        tmp_path,
        allow_write=True,
    )

    change = FakeChange(
        path="example.py",
        old_text="value = 999",
        new_text="value = 2",
    )

    with pytest.raises(ValueError):
        executor.apply_change(change)

    assert target.read_text(
        encoding="utf-8"
    ) == "value = 1\n"


def test_apply_change_rejects_duplicate_old_text(tmp_path):
    target = Path(tmp_path) / "example.py"
    target.write_text(
        "value = 1\nvalue = 1\n",
        encoding="utf-8",
    )

    executor = make_executor(
        tmp_path,
        allow_write=True,
    )

    change = FakeChange(
        path="example.py",
        old_text="value = 1",
        new_text="value = 2",
    )

    with pytest.raises(ValueError):
        executor.apply_change(change)

    assert target.read_text(
        encoding="utf-8"
    ) == "value = 1\nvalue = 1\n"


def test_apply_change_rejects_path_outside_workspace(tmp_path):
    outside_file = Path(tmp_path).parent / "outside.py"
    outside_file.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    executor = make_executor(
        tmp_path,
        allow_write=True,
    )

    change = FakeChange(
        path="../outside.py",
        old_text="value = 1",
        new_text="value = 2",
    )

    with pytest.raises(PermissionError):
        executor.apply_change(change)

    assert outside_file.read_text(
        encoding="utf-8"
    ) == "value = 1\n"

from pathlib import Path

import pytest

from agents.coding.editor import CodingEditor
from agents.coding.permissions import CodingPermissions


def make_editor(tmp_path, allow_write=False):
    permissions = CodingPermissions(
        allow_read=True,
        allow_search=True,
        allow_list=True,
        allow_write=allow_write,
        allow_tests=False,
        allow_git=False,
    )

    return CodingEditor(
        tmp_path,
        permissions=permissions,
    )


def test_write_file_requires_permission(tmp_path):
    target = Path(tmp_path) / "example.py"
    target.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    editor = make_editor(
        tmp_path,
        allow_write=False,
    )

    with pytest.raises(PermissionError):
        editor.write_file(
            "example.py",
            "value = 2\n",
        )

    assert target.read_text(
        encoding="utf-8"
    ) == "value = 1\n"


def test_write_file_replaces_contents(tmp_path):
    target = Path(tmp_path) / "example.py"
    target.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    editor = make_editor(
        tmp_path,
        allow_write=True,
    )

    result = editor.write_file(
        "example.py",
        "value = 2\n",
    )

    assert result["success"] is True
    assert result["path"] == "example.py"
    assert target.read_text(
        encoding="utf-8"
    ) == "value = 2\n"


def test_write_file_rejects_missing_file(tmp_path):
    editor = make_editor(
        tmp_path,
        allow_write=True,
    )

    with pytest.raises(FileNotFoundError):
        editor.write_file(
            "missing.py",
            "value = 2\n",
        )


def test_write_file_rejects_path_outside_root(tmp_path):
    outside_file = Path(tmp_path).parent / "outside.py"
    outside_file.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    editor = make_editor(
        tmp_path,
        allow_write=True,
    )

    with pytest.raises(PermissionError):
        editor.write_file(
            "../outside.py",
            "value = 2\n",
        )

    assert outside_file.read_text(
        encoding="utf-8"
    ) == "value = 1\n"


def test_replace_text_replaces_exact_occurrence(tmp_path):
    target = Path(tmp_path) / "example.py"
    target.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    editor = make_editor(
        tmp_path,
        allow_write=True,
    )

    result = editor.replace_text(
        "example.py",
        "value = 1",
        "value = 2",
    )

    assert result["success"] is True
    assert result["path"] == "example.py"
    assert target.read_text(
        encoding="utf-8"
    ) == "value = 2\n"


def test_replace_text_rejects_missing_old_text(tmp_path):
    target = Path(tmp_path) / "example.py"
    target.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    editor = make_editor(
        tmp_path,
        allow_write=True,
    )

    with pytest.raises(ValueError):
        editor.replace_text(
            "example.py",
            "value = 999",
            "value = 2",
        )

    assert target.read_text(
        encoding="utf-8"
    ) == "value = 1\n"


def test_replace_text_rejects_duplicate_old_text(tmp_path):
    target = Path(tmp_path) / "example.py"
    target.write_text(
        "value = 1\nvalue = 1\n",
        encoding="utf-8",
    )

    editor = make_editor(
        tmp_path,
        allow_write=True,
    )

    with pytest.raises(ValueError):
        editor.replace_text(
            "example.py",
            "value = 1",
            "value = 2",
        )

    assert target.read_text(
        encoding="utf-8"
    ) == "value = 1\nvalue = 1\n"

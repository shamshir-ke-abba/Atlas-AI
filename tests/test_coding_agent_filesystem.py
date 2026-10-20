"""Tests for Atlas Coding Agent safe filesystem tools, boundaries, and execution loop."""

from pathlib import Path
import pytest

from agents.coding.agent import CodingAgent
from agents.coding.detector import CodingTaskDetector
from agents.coding.permissions import CodingPermissions
from agents.coding.tools.filesystem import CodeFilesystem
from ai.brain import AtlasBrain


# ==========================================================
# FILESYSTEM TOOL TESTS
# ==========================================================

def test_filesystem_write_and_read(tmp_path):
    fs = CodeFilesystem(tmp_path, allow_write=True)

    # Write new file
    res = fs.write_file("test.txt", "Hello World")
    assert res["success"] is True
    assert (tmp_path / "test.txt").exists()
    assert (tmp_path / "test.txt").read_text(encoding="utf-8") == "Hello World"

    # Read back
    content = fs.read_file("test.txt")
    assert content == "Hello World"


def test_filesystem_list_files(tmp_path):
    fs = CodeFilesystem(tmp_path, allow_write=True)

    (tmp_path / "file1.txt").write_text("1")
    (tmp_path / "file2.py").write_text("2")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "subfile.txt").write_text("3")

    # Ignored directories
    (tmp_path / ".git").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / "__pycache__").mkdir()

    items = fs.list_files(".")
    names = [i["name"] for i in items]

    assert "file1.txt" in names
    assert "file2.py" in names
    assert "subdir" in names
    assert ".git" not in names
    assert ".venv" not in names
    assert "__pycache__" not in names


def test_filesystem_edit_file(tmp_path):
    fs = CodeFilesystem(tmp_path, allow_write=True)

    fs.write_file("doc.txt", "Initial content")
    assert fs.read_file("doc.txt") == "Initial content"

    # Exact replacement
    res = fs.edit_file(
        "doc.txt",
        old_text="Initial content",
        new_text="Initial content — modified successfully",
    )
    assert res["success"] is True
    assert (
        fs.read_file("doc.txt")
        == "Initial content — modified successfully"
    )


def test_filesystem_edit_file_full_replace(tmp_path):
    fs = CodeFilesystem(tmp_path, allow_write=True)

    fs.write_file("doc.txt", "Alpha")
    fs.edit_file("doc.txt", old_text=None, new_text="Beta")
    assert fs.read_file("doc.txt") == "Beta"


def test_filesystem_edit_file_rejects_missing_target_text(tmp_path):
    fs = CodeFilesystem(tmp_path, allow_write=True)

    fs.write_file("doc.txt", "Hello")
    with pytest.raises(ValueError, match="not found"):
        fs.edit_file("doc.txt", old_text="NonExistent", new_text="World")


def test_filesystem_create_directory(tmp_path):
    fs = CodeFilesystem(tmp_path, allow_write=True)

    res = fs.create_directory("deep/nested/dir")
    assert res["success"] is True
    assert (tmp_path / "deep/nested/dir").is_dir()


def test_filesystem_search_files(tmp_path):
    fs = CodeFilesystem(tmp_path, allow_write=True)

    fs.write_file("search1.py", "def target_function(): pass")
    fs.write_file("search2.py", "x = 42")

    matches = fs.search_files("target_function")
    assert "target_function" in matches
    assert "search1.py" in matches


def test_filesystem_search_files_option_like_query(tmp_path):
    fs = CodeFilesystem(tmp_path, allow_write=True)

    # Write files containing option-like text
    fs.write_file("cli.py", "parser.add_argument('--version', action='store_true')")
    fs.write_file("flags.py", "FLAG_HELP = '--help'")
    fs.write_file("other.py", "CONSTANT = 100")

    # Search for option-like strings that would normally be flags for ripgrep
    matches_version = fs.search_files("--version")
    assert "--version" in matches_version
    assert "cli.py" in matches_version

    matches_help = fs.search_files("--help")
    assert "--help" in matches_help
    assert "flags.py" in matches_help

    # Verify unrelated files are not matched
    assert "other.py" not in matches_version


def test_filesystem_get_absolute_path(tmp_path):
    fs = CodeFilesystem(tmp_path)
    fs.write_file("item.txt", "content")

    abs_p = fs.get_absolute_path("item.txt")
    assert abs_p == str((tmp_path / "item.txt").resolve())


# ==========================================================
# SECURITY & BOUNDARY TESTS
# ==========================================================

def test_filesystem_rejects_escape_via_dot_dot(tmp_path):
    fs = CodeFilesystem(tmp_path, allow_write=True)

    with pytest.raises(PermissionError, match="outside workspace"):
        fs.read_file("../escape.txt")

    with pytest.raises(PermissionError, match="outside workspace"):
        fs.write_file("../escape.txt", "malicious")

    with pytest.raises(PermissionError, match="outside workspace"):
        fs.list_files("../../")


def test_filesystem_rejects_absolute_path_outside_workspace(tmp_path):
    fs = CodeFilesystem(tmp_path, allow_write=True)

    with pytest.raises(PermissionError, match="outside workspace"):
        fs.read_file("/etc/passwd")

    with pytest.raises(PermissionError, match="outside workspace"):
        fs.write_file("/tmp/malicious_write.txt", "data")


def test_filesystem_allows_absolute_path_inside_workspace(tmp_path):
    fs = CodeFilesystem(tmp_path, allow_write=True)
    inside_path = (tmp_path / "valid.txt").resolve()

    res = fs.write_file(str(inside_path), "inside content")
    assert res["success"] is True
    assert fs.read_file(str(inside_path)) == "inside content"


def test_filesystem_enforces_write_permission(tmp_path):
    fs = CodeFilesystem(tmp_path, allow_write=False)

    (tmp_path / "readonly.txt").write_text("initial")

    with pytest.raises(PermissionError, match="Write operations are disabled"):
        fs.write_file("readonly.txt", "new data")

    with pytest.raises(PermissionError, match="Write operations are disabled"):
        fs.edit_file("readonly.txt", "initial", "changed")

    with pytest.raises(PermissionError, match="Write operations are disabled"):
        fs.create_directory("new_dir")


def test_filesystem_enforces_test_permission(tmp_path):
    fs = CodeFilesystem(tmp_path, allow_tests=False)

    with pytest.raises(PermissionError, match="Running tests is disabled"):
        fs.run_tests()


# ==========================================================
# CODING AGENT TOOL DISPATCH & NORMALIZATION TESTS
# ==========================================================

def test_coding_agent_execute_tool_normalization(tmp_path):
    agent = CodingAgent(workspace=tmp_path)

    # write_file with 'file' and 'text' aliases
    agent.execute_tool(
        "write_file",
        {"file": "alias.txt", "text": "Alias content"},
    )
    assert (tmp_path / "alias.txt").read_text() == "Alias content"

    # read_file with 'filename' alias
    content = agent.execute_tool(
        "read_file",
        {"filename": "alias.txt"},
    )
    assert content == "Alias content"

    # edit_file with 'find' and 'replace' aliases
    agent.execute_tool(
        "edit_file",
        {
            "file": "alias.txt",
            "find": "Alias content",
            "replace": "Updated content",
        },
    )
    assert (tmp_path / "alias.txt").read_text() == "Updated content"


def test_coding_agent_extract_actions():
    sample_text = """
ACTION: write_file
ARGUMENTS: {"path": "atlas_fs_test.txt", "content": "Initial content"}
"""
    actions, final_ans = CodingAgent.extract_actions_and_final(sample_text)
    assert len(actions) == 1
    assert actions[0][0] == "write_file"
    assert actions[0][1] == {
        "path": "atlas_fs_test.txt",
        "content": "Initial content",
    }
    assert final_ans is None


def test_coding_agent_extract_actions_with_argments_typo():
    sample_text = """
ACTION: edit_file
ARGMENTS: {"path": "test.txt", "old_text": "a", "new_text": "b"}
"""
    actions, final_ans = CodingAgent.extract_actions_and_final(sample_text)
    assert len(actions) == 1
    assert actions[0][0] == "edit_file"
    assert actions[0][1]["old_text"] == "a"


def test_coding_agent_extract_final_answer():
    sample_text = """
FINAL_ANSWER: All operations completed successfully. File path: /home/test/file.txt
"""
    actions, final_ans = CodingAgent.extract_actions_and_final(sample_text)
    assert len(actions) == 0
    assert "All operations completed successfully" in final_ans


# ==========================================================
# CODING TASK DETECTOR TESTS
# ==========================================================

def test_detector_detects_filesystem_prompts():
    detector = CodingTaskDetector()

    assert detector.is_coding_task(
        "List the files and folders in current directory."
    )
    assert detector.is_coding_task(
        "Create a file named atlas_fs_test.txt containing 'Initial content'."
    )
    assert detector.is_coding_task(
        "Modify the file so it contains 'Initial content — modified successfully'."
    )
    assert detector.is_coding_task(
        "Read the file and show its contents."
    )


# ==========================================================
# BRAIN ROUTING TESTS
# ==========================================================

def test_brain_routes_coding_task_to_coding_agent(tmp_path):
    class FakeCodingAgent:
        def __init__(self):
            self.called_stream = False
            self.called_run = False

        def stream_run(self, task):
            self.called_stream = True
            yield "Executed step 1"
            yield "Final answer"

        def run(self, task):
            self.called_run = True
            return "Executed synchronously"

    fake_agent = FakeCodingAgent()
    brain = AtlasBrain()
    brain.coding_agent = fake_agent

    # Test stream_message routing
    chunks = list(
        brain.stream_message(
            "Create a file named atlas_fs_test.txt with 'Initial content'"
        )
    )
    assert fake_agent.called_stream is True
    assert "Executed step 1" in chunks

    # Test synchronous _route_message routing
    handler = brain._route_message(
        "Create a file named atlas_fs_test.txt with 'Initial content'"
    )
    res = handler("Create a file...", {})
    assert fake_agent.called_run is True
    assert res == "Executed synchronously"

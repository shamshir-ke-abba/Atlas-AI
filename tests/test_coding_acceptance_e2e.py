"""Mandatory Acceptance Integration Test for Atlas Coding Agent (Phase 5).

Verifies the exact multi-step filesystem test prompt through the real application
execution path (FastAPI Web Chat API) without mocks.
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient
from interfaces.web.server import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_FILE = PROJECT_ROOT / "atlas_fs_test.txt"
EXPECTED_CONTENT = "Initial content — modified successfully"
CANONICAL_PATH = str(TEST_FILE)

PROMPT = """Perform the following tasks in the current directory:
1. List the files and folders in this directory.
2. Create a file named atlas_fs_test.txt containing exactly the text 'Initial content'.
3. Read the file and show its exact contents.
4. Modify the file so it contains exactly 'Initial content — modified successfully'.
5. Read the file again and show the updated contents.
6. Report the absolute path of the file."""


def test_mandatory_acceptance_filesystem_e2e():
    # Ensure clean slate
    if TEST_FILE.exists():
        TEST_FILE.unlink()

    client = TestClient(app)

    try:
        response = client.post(
            "/api/chat",
            json={"message": PROMPT},
        )
        assert response.status_code == 200

        # Parse streamed ndjson response
        streamed_chunks = []
        for line in response.text.strip().split("\n"):
            if line.strip():
                try:
                    evt = json.loads(line)
                    if evt.get("type") == "chunk":
                        streamed_chunks.append(evt.get("text", ""))
                except Exception:
                    pass

        full_output = "".join(streamed_chunks).strip()

        # 1. Verify file exists on disk
        assert TEST_FILE.exists(), "Mandatory test file atlas_fs_test.txt was not created on disk."

        # 2. Verify file contains exact modified content
        actual_content = TEST_FILE.read_text(encoding="utf-8")
        assert actual_content == EXPECTED_CONTENT, (
            f"Content mismatch! Expected: {repr(EXPECTED_CONTENT)}, got: {repr(actual_content)}"
        )

        # 3. Verify no unexecuted shell blocks
        assert not ("```bash" in full_output and not TEST_FILE.exists())

        # 4. Verify path and content reported in streamed output
        assert CANONICAL_PATH in full_output or "atlas_fs_test.txt" in full_output
        assert "Initial content" in full_output

    finally:
        # Clean up
        if TEST_FILE.exists():
            TEST_FILE.unlink()

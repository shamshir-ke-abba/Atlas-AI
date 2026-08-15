import json
from pathlib import Path
import shutil
import tempfile
from core.memory import MemoryManager
from config import MEMORY_FILE


def backup_memory():
    orig = Path(MEMORY_FILE)
    if orig.exists():
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.close()
        shutil.copy(orig, tmp.name)
        return tmp.name
    return None


def restore_memory(backup_path):
    orig = Path(MEMORY_FILE)
    if backup_path is None:
        # remove file if it didn't exist before
        try:
            if orig.exists():
                orig.unlink()
        except Exception:
            pass
    else:
        shutil.copy(backup_path, orig)
        try:
            Path(backup_path).unlink()
        except Exception:
            pass


def test_memory_save_reload_update_forget():
    backup = backup_memory()

    try:
        m = MemoryManager()

        # Ensure clean state
        m.clear()

        # Save
        m.remember("identity", "name", "Saad")
        assert m.recall("identity", "name") == "Saad"

        # Reload
        m2 = MemoryManager()
        assert m2.recall("identity", "name") == "Saad"

        # Update
        m2.remember("identity", "name", "Alex")
        assert m2.recall("identity", "name") == "Alex"

        m2.remember("identity", "name", "Saad")
        assert m2.recall("identity", "name") == "Saad"

        # Forget
        m2.forget("identity", "name")
        assert m2.recall("identity", "name") is None

    finally:
        restore_memory(backup)


def test_extract_from_message_and_persistence():
    backup = backup_memory()

    try:
        m = MemoryManager()
        m.clear()

        # Simulate user saying "My name is Saad"
        m.extract_from_message("My name is Saad")
        assert m.recall("identity", "name") == "Saad"

        # restart
        m2 = MemoryManager()
        assert m2.recall("identity", "name") == "Saad"

        # Hallucination protection: if model says "Your name is Alex",
        # we should not persist that. Do not call extract_from_message.
        # Simulate potential bad flow by intentionally not invoking remember.
        m3 = MemoryManager()
        # Ensure no accidental storage happened
        assert m3.recall("identity", "name") == "Saad"

    finally:
        restore_memory(backup)


def test_explicit_remember_command_simulation():
    backup = backup_memory()

    try:
        m = MemoryManager()
        m.clear()

        # Simulate explicit remember phrasing
        m.extract_from_message("Remember that my favorite color is blue.")
        assert m.recall("preferences", "favorite_color") == "blue"

    finally:
        restore_memory(backup)

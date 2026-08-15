import sys
from pathlib import Path
import tempfile
import shutil

# Ensure project root is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.memory import MemoryManager
from ai.brain import AtlasBrain


class FakeModel:
    def __init__(self, reply=None):
        self.reply = reply

    def generate(self, prompt, stream=True):
        if self.reply is None:
            return []
        # If streaming, yield chunks
        if stream:
            for ch in [self.reply]:
                yield ch
        else:
            return self.reply

    def cancel_current(self):
        pass


def make_temp_memory_file():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    return Path(tmp.name)


def test_brain_remember_recall_forget_stream_and_restart():
    # Create a temporary memory file and point core.memory to it
    import core.memory as core_memory

    tmp_path = make_temp_memory_file()
    core_memory.MEMORY_FILE = tmp_path

    # Instantiate MemoryManager and Brain
    m1 = MemoryManager()
    brain1 = AtlasBrain(model=FakeModel(), memory=m1)

    # Test A: remember name
    resp = brain1.process_message("My name is Saad")
    assert m1.recall("identity", "name") == "Saad"

    # Simulate restart
    del brain1
    del m1

    m2 = MemoryManager()
    brain2 = AtlasBrain(model=FakeModel(), memory=m2)

    resp2 = brain2.process_message("What is my name?")
    assert "Saad" in resp2

    # Test B: remember favorite color
    resp = brain2.process_message("Remember that my favorite color is blue")
    assert m2.recall("preferences", "favorite_color") == "blue"

    # Restart
    del brain2
    del m2

    m3 = MemoryManager()
    brain3 = AtlasBrain(model=FakeModel(), memory=m3)

    resp3 = brain3.process_message("What is my favorite color?")
    assert "blue" in resp3

    # Test C: forget favorite color
    resp_forget = brain3.process_message("Forget my favorite color")
    # memory must be actually removed
    assert m3.recall("preferences", "favorite_color") is None

    # After forgetting, the brain should say it doesn't have it saved
    resp_after = brain3.process_message("What is my favorite color?")
    ra = (resp_after or "").lower()
    ok = ("don't" in ra) or ("do not" in ra) or ("i don't" in ra) or ("i do not" in ra)
    if not ok:
        raise AssertionError(f"Unexpected resp_after: {repr(resp_after)}")

    # Test D: hallucination protection
    # Use a model that hallucinates a name
    m4 = MemoryManager()
    # Ensure memory is clean for this hallucination protection test
    m4.clear()
    brain4 = AtlasBrain(model=FakeModel(reply="Your name is Alex."), memory=m4)

    # Ask a non-memory question so the model is used and hallucinate
    resp_h = brain4.process_message("Tell me something")
    # Ensure hallucination was not written to memory
    assert m4.recall("identity", "name") is None

    # Test stream_message path for remember
    m5 = MemoryManager()
    brain5 = AtlasBrain(model=FakeModel(), memory=m5)

    gen = brain5.stream_message("My name is Saad")
    parts = list(gen)
    assert m5.recall("identity", "name") == "Saad"

    # Cleanup temp file
    try:
        tmp_path.unlink()
    except Exception:
        pass


if __name__ == '__main__':
    test_brain_remember_recall_forget_stream_and_restart()
    print('All brain-memory tests passed')

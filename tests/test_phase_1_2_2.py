import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest

from ai.brain import AtlasBrain
from core.memory import MemoryManager


class FakeModel:
    def __init__(self, reply=None):
        self.reply = reply

    def generate(self, prompt, stream=True):
        if self.reply is None:
            return []
        if stream:
            for ch in [self.reply]:
                yield ch
        else:
            return self.reply

    def cancel_current(self):
        pass


@pytest.fixture
def isolated_memory(tmp_path):
    import core.memory as core_memory

    old = core_memory.MEMORY_FILE
    core_memory.MEMORY_FILE = tmp_path / "memory.json"
    m = MemoryManager()
    m.clear()
    yield m
    core_memory.MEMORY_FILE = old


def test_phase_1_2_2_natural_project_extraction(isolated_memory):
    isolated_memory.extract_from_message(
        "I'm building an AI assistant called Atlas in Python."
    )

    assert isolated_memory.recall("projects", "project_name") == "Atlas"
    assert isolated_memory.recall("projects", "technology") == "Python"


def test_phase_1_2_2_preference_extraction(isolated_memory):
    isolated_memory.extract_from_message(
        "I prefer explanations from first principles."
    )

    assert (
        isolated_memory.recall("preferences", "explanation_style")
        == "first principles"
    )


def test_phase_1_2_2_environment_extraction(isolated_memory):
    isolated_memory.extract_from_message("I use Ubuntu.")

    assert isolated_memory.recall("environment", "operating_system") == "Ubuntu"


def test_phase_1_2_2_no_extraction_from_questions(isolated_memory):
    isolated_memory.extract_from_message("What is Python?")

    assert isolated_memory.recall("projects", "project_name") is None
    assert isolated_memory.recall("environment", "operating_system") is None
    assert isolated_memory.recall("preferences", "explanation_style") is None


def test_phase_1_2_2_no_extraction_from_temporary_statements(isolated_memory):
    isolated_memory.extract_from_message("I'm tired today.")

    assert isolated_memory.recall("identity", "name") is None
    assert isolated_memory.recall("preferences", "explanation_style") is None


def test_phase_1_2_2_duplicate_prevention(isolated_memory):
    isolated_memory.extract_from_message(
        "I'm building Atlas in Python."
    )
    isolated_memory.extract_from_message(
        "My project Atlas is written in Python."
    )

    assert isolated_memory.recall("projects", "project_name") == "Atlas"
    assert isolated_memory.recall("projects", "technology") == "Python"

    projects = isolated_memory.all().get("projects", {})
    assert len(projects) <= 2


def test_phase_1_2_2_relevance_filtering(isolated_memory):
    isolated_memory.remember("identity", "name", "Saad")
    isolated_memory.remember("projects", "project_name", "Atlas")
    isolated_memory.remember("projects", "technology", "Python")
    isolated_memory.remember("preferences", "favorite_color", "blue")
    isolated_memory.remember("environment", "operating_system", "Ubuntu")

    rel = isolated_memory.relevant("How should I structure my Python project?")

    assert rel.get("projects", {}).get("project_name") == "Atlas"
    assert rel.get("projects", {}).get("technology") == "Python"
    assert rel.get("preferences", {}).get("favorite_color") is None
    assert rel.get("environment", {}).get("operating_system") is None


def test_phase_1_2_2_irrelevant_query_omits_memory(isolated_memory):
    isolated_memory.remember("identity", "name", "Saad")
    isolated_memory.remember("projects", "project_name", "Atlas")
    isolated_memory.remember("projects", "technology", "Python")

    rel = isolated_memory.relevant("Explain gravity.")

    assert rel == {}


def test_phase_1_2_2_hallucination_protection(isolated_memory):
    brain = AtlasBrain(model=FakeModel(reply="Your name is Alex."), memory=isolated_memory)

    brain.process_message("Tell me something")

    assert isolated_memory.recall("identity", "name") is None


def test_phase_1_2_2_explicit_remember_and_forget_still_work(isolated_memory):
    brain = AtlasBrain(model=FakeModel(), memory=isolated_memory)

    resp = brain.process_message("Remember that my name is Saad")
    assert "saved" in (resp or "").lower()
    assert isolated_memory.recall("identity", "name") == "Saad"

    resp2 = brain.process_message("Forget my name")
    assert "forgot" in (resp2 or "").lower()
    assert isolated_memory.recall("identity", "name") is None

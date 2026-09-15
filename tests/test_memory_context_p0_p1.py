"""
Atlas AI V3 — Phase P0 & P1 Regression Test Suite
=================================================

Validates:
- P0.1: Removal of 8-message context cliff and respect of config.MAX_HISTORY
- P0.2: Fact queries return human-readable values, never internal dictionary keys
- P0.3: Multi-word name extraction (single, multi, Hinglish, boundaries, sentence continuation)
- P0.4: Authoritative system prompt unification via ai/prompts.py
- P1.1: Synonym-aware and attribute-based memory retrieval (no keyword blindness)
- P1.2: Over-fetching prevention (querying for one preference retrieves only that preference)
- P1.3: Relevance scoring and noise filtering (unrelated queries return empty memory)
- P1.4: Better extraction with negation safety (negated facts are never saved)
- Persistence: Full backward compatibility with existing data/memory.json schema
"""

import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import MAX_HISTORY
import core.memory as core_memory
from core.memory import MemoryManager
from ai.prompts import SYSTEM_PROMPT
from ai.context_builder import ContextBuilder
from ai.brain import AtlasBrain


class Sandbox:
    """Isolated test environment to ensure production memory is never touched."""

    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="atlas_p0_p1_test_")
        self.mem_file = Path(self.dir) / "memory.json"
        self._orig_file = core_memory.MEMORY_FILE
        core_memory.MEMORY_FILE = self.mem_file

    def get_memory(self) -> MemoryManager:
        return MemoryManager(memory_file=self.mem_file)

    def cleanup(self):
        core_memory.MEMORY_FILE = self._orig_file
        shutil.rmtree(self.dir, ignore_errors=True)


class MockModel:
    def __init__(self, reply="Mock reply"):
        self.reply = reply
        self.last_prompt = ""

    def generate(self, prompt: str, stream: bool = False):
        self.last_prompt = prompt
        if stream:
            yield self.reply
        else:
            return self.reply

    def cancel_current(self):
        pass


# ==============================================================================
# 1. MEMORY TESTS (P0.3, P1.1, P1.2, P1.3, P1.4)
# ==============================================================================

class TestMemoryIntelligence:

    @pytest.fixture(autouse=True)
    def setup_env(self):
        self.sandbox = Sandbox()
        self.mem = self.sandbox.get_memory()
        yield
        self.sandbox.cleanup()

    def test_single_word_name(self):
        self.mem.extract_from_message("My name is Saad")
        assert self.mem.recall("identity", "name") == "Saad"

        self.mem.extract_from_message("Call me Alex")
        assert self.mem.recall("identity", "name") == "Alex"

    def test_multi_word_name(self):
        # P0.3: Multi-word English full name
        self.mem.extract_from_message("My name is Saad Khan")
        assert self.mem.recall("identity", "name") == "Saad Khan"

        self.mem.extract_from_message("Call me John Doe")
        assert self.mem.recall("identity", "name") == "John Doe"

        # Sentence continuation boundary
        self.mem.extract_from_message("My name is Saad Khan and I am a software engineer")
        assert self.mem.recall("identity", "name") == "Saad Khan"

        # Punctuation boundary
        self.mem.extract_from_message("My name is Saad Khan.")
        assert self.mem.recall("identity", "name") == "Saad Khan"

    def test_hinglish_name(self):
        # P0.3: Hinglish forms
        self.mem.extract_from_message("Mera naam Saad Khan hai")
        assert self.mem.recall("identity", "name") == "Saad Khan"

        self.mem.extract_from_message("Mera naam Alex hai")
        assert self.mem.recall("identity", "name") == "Alex"

    def test_memory_update(self):
        # Initial city
        self.mem.extract_from_message("I live in Mumbai")
        assert self.mem.recall("identity", "city") == "Mumbai"

        # P1.4: Relocation / moving phrasing updates city
        self.mem.extract_from_message("I moved to Berlin")
        assert self.mem.recall("identity", "city") == "Berlin"

        # Color update
        self.mem.extract_from_message("My favorite color is blue")
        assert self.mem.recall("preferences", "favorite_color") == "blue"

        self.mem.extract_from_message("My favorite color is now purple")
        assert self.mem.recall("preferences", "favorite_color") == "purple"

    def test_memory_recall(self):
        self.mem.remember("identity", "name", "Saad")
        self.mem.remember("identity", "city", "Mumbai")

        rel_name = self.mem.relevant("What is my name?")
        assert "identity" in rel_name
        assert rel_name["identity"].get("name") == "Saad"

        rel_city = self.mem.relevant("Where do I live?")
        assert "identity" in rel_city
        assert rel_city["identity"].get("city") == "Mumbai"

    def test_fact_query_returns_values(self):
        # P0.2: Fact queries return values, never keys
        self.mem.remember("facts", "fact_101", "User owns a Golden Retriever named Rex")
        self.mem.remember("facts", "fact_102", "User works remotely on Mondays")

        brain = AtlasBrain(model=MockModel(), memory=self.mem)
        response = brain.process_message("What do you remember?")

        # Must contain the human-readable text
        assert "Rex" in response or "Mondays" in response
        # Must NOT leak internal IDs
        assert "fact_101" not in response
        assert "fact_102" not in response

    def test_specific_preference_retrieval(self):
        # P1.2: Over-fetching prevention
        self.mem.remember("preferences", "favorite_color", "blue")
        self.mem.remember("preferences", "favorite_food", "pizza")
        self.mem.remember("preferences", "explanation_style", "concise")
        self.mem.remember("preferences", "favorite_anime", "One Piece")

        rel = self.mem.relevant("What is my favorite color?")
        assert "preferences" in rel
        # Must contain ONLY favorite_color
        assert "favorite_color" in rel["preferences"]
        assert rel["preferences"]["favorite_color"] == "blue"
        # Must NOT leak unrelated preferences!
        assert "favorite_food" not in rel["preferences"]
        assert "explanation_style" not in rel["preferences"]
        assert "favorite_anime" not in rel["preferences"]

    def test_location_synonyms(self):
        # P1.1: Semantic synonym retrieval without keyword blindness
        self.mem.remember("identity", "city", "Mumbai")

        # Synonym 1: "staying"
        rel1 = self.mem.relevant("Where am I currently staying?")
        assert "identity" in rel1
        assert rel1["identity"].get("city") == "Mumbai"

        # Synonym 2: "based in"
        rel2 = self.mem.relevant("Which city am I based in?")
        assert "identity" in rel2
        assert rel2["identity"].get("city") == "Mumbai"

        # Synonym 3: "reside"
        rel3 = self.mem.relevant("Where do I reside?")
        assert "identity" in rel3
        assert rel3["identity"].get("city") == "Mumbai"

    def test_unrelated_memory_is_not_returned(self):
        # P1.3: Unrelated queries return empty memory
        self.mem.remember("identity", "city", "Mumbai")
        self.mem.remember("preferences", "favorite_color", "blue")
        self.mem.remember("environment", "operating_system", "Linux")

        rel = self.mem.relevant("What is the capital of France?")
        assert rel == {}

        rel2 = self.mem.relevant("Can you explain how quicksort works in Python?")
        assert rel2 == {}

    def test_broad_memory_query_is_bounded(self):
        # P1.2: Broad queries return bounded summary, not 100% database dump
        for i in range(10):
            self.mem.remember("preferences", f"item_{i}", f"val_{i}")
        for i in range(10):
            self.mem.remember("facts", f"fact_{i}", f"Random fact number {i}")

        rel = self.mem.relevant("What do you know about me?")
        total_items = sum(len(v) if isinstance(v, dict) else 1 for v in rel.values())
        assert total_items <= 5, f"Broad query exceeded bounded limit: got {total_items} items"

    def test_negated_fact_not_saved(self):
        # P1.4: Negation safety
        self.mem.extract_from_message("I am not from Mumbai")
        assert self.mem.recall("identity", "city") is None

        self.mem.extract_from_message("I don't live in Mumbai")
        assert self.mem.recall("identity", "city") is None

        self.mem.extract_from_message("I don't like coffee")
        all_data = self.mem.all()
        assert "coffee" not in str(all_data)


# ==============================================================================
# 2. CONTEXT TESTS (P0.1, P0.4)
# ==============================================================================

class TestContextBuilderIntelligence:

    def test_history_beyond_8_messages(self):
        # P0.1: Context cliff removed — history > 8 messages retained
        builder = ContextBuilder(max_history=20)
        target = "TARGET_SECRET_ALPHA = 999"

        # Build history with 15 messages (turn 0 to 14)
        history = [{"sender": "user", "text": target, "is_user": True}]
        for i in range(13):
            history.append({"sender": "atlas" if i % 2 == 0 else "user", "text": f"Turn {i}", "is_user": (i % 2 != 0)})

        prompt = builder.build(history, "What is the secret?")
        # Must retain target fact even though it is at distance 14 (greater than 8!)
        assert target in prompt, "P0.1 FAILURE: Message at distance 14 was pruned by history clamp!"

    def test_max_history_configuration_respected(self):
        # P0.1: Config MAX_HISTORY respected
        builder = ContextBuilder()
        # Default should match config.MAX_HISTORY (20), not 8!
        assert builder.max_history == int(MAX_HISTORY or 20)
        assert builder.max_history >= 20

    def test_current_message_present(self):
        builder = ContextBuilder()
        prompt = builder.build([], "Ping test message")
        assert "Ping test message" in prompt
        assert "===== CURRENT USER MESSAGE =====" in prompt

    def test_recent_history_present(self):
        builder = ContextBuilder()
        history = [
            {"sender": "user", "text": "Hello Atlas", "is_user": True},
            {"sender": "atlas", "text": "Hello! How can I help you?", "is_user": False},
        ]
        prompt = builder.build(history, "Tell me a joke")
        assert "User: Hello Atlas" in prompt
        assert "Atlas: Hello! How can I help you?" in prompt

    def test_relevant_memory_present(self):
        builder = ContextBuilder()
        memory = {"identity": {"city": "Mumbai"}, "preferences": {"favorite_color": "blue"}}
        prompt = builder.build([], "Where do I live?", memory=memory)
        assert "===== RELEVANT PERSISTENT MEMORY =====" in prompt
        assert "city: Mumbai" in prompt
        assert "favorite_color: blue" in prompt

    def test_irrelevant_memory_absent(self):
        builder = ContextBuilder()
        prompt = builder.build([], "Hello", memory={})
        assert "(No relevant persistent memory.)" in prompt

    def test_system_prompt_is_authoritative(self):
        # P0.4: System prompt matches ai/prompts.py
        builder = ContextBuilder()
        prompt = builder.build([], "Test")
        assert SYSTEM_PROMPT in prompt

    def test_no_duplicate_system_prompt(self):
        # P0.4: Only one system prompt block in assembled prompt
        builder = ContextBuilder()
        prompt = builder.build([], "Test")
        occurrences = prompt.count("You are Atlas")
        assert occurrences == 1, f"Expected exactly 1 system prompt declaration, found {occurrences}"


# ==============================================================================
# 3. PERSISTENCE & BACKWARD COMPATIBILITY
# ==============================================================================

class TestPersistenceAndCompatibility:

    def test_memory_persistence(self):
        sandbox = Sandbox()
        try:
            m1 = sandbox.get_memory()
            m1.remember("identity", "name", "Saad Khan")
            m1.remember("identity", "city", "Berlin")
            m1.remember("preferences", "favorite_anime", "One Piece")

            # Reload from disk
            m2 = MemoryManager(memory_file=sandbox.mem_file)
            assert m2.recall("identity", "name") == "Saad Khan"
            assert m2.recall("identity", "city") == "Berlin"
            assert m2.recall("preferences", "favorite_anime") == "One Piece"
        finally:
            sandbox.cleanup()

    def test_existing_memory_schema_compatibility(self):
        # Verifies old 6-category schema format loads and saves seamlessly
        sandbox = Sandbox()
        try:
            old_schema = {
                "identity": {"name": "Saad"},
                "preferences": {"favorite_color": "blue"},
                "projects": {"project_name": "The Other Side"},
                "environment": {"operating_system": "Ubuntu"},
                "facts": {"1": "owns a cat"},
                "goals": {}
            }
            import json
            with open(sandbox.mem_file, "w", encoding="utf-8") as f:
                json.dump(old_schema, f)

            m = MemoryManager(memory_file=sandbox.mem_file)
            assert m.recall("identity", "name") == "Saad"
            assert m.recall("environment", "operating_system") == "Ubuntu"
            assert m.recall("facts", "1") == "owns a cat"

            # Query should work seamlessly on old data
            rel = m.relevant("What system do I use?")
            assert "environment" in rel
            assert rel["environment"].get("operating_system") == "Ubuntu"
        finally:
            sandbox.cleanup()

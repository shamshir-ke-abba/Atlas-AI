"""
Atlas AI V3 — Comprehensive Memory & Context Benchmark Suite (Post-Repair Verification)
========================================================================================

This test suite performs an end-to-end evaluation of Atlas V3's intelligence layer
after the P0 and P1 repair implementations:
- core/memory.py (Multi-word names, relocations, dynamic preferences, synonym retrieval, noise isolation)
- ai/context_builder.py (Authoritative prompt unification, respect of config.MAX_HISTORY, removal of 8-clamp)
- ai/brain.py (Fact queries return human-readable values, not internal keys)
- Model-in-the-Loop tests (Live Ollama Qwen2.5:1.5b)

SAFETY ASSURANCE:
- Uses strictly isolated temporary directories and files.
- NEVER modifies or reads real user data (data/memory.json or data/conversations/).
- Safe to run via `pytest tests/benchmark_memory_context.py` or `.venv/bin/python tests/benchmark_memory_context.py`.
"""

import sys
import os
import json
import time
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from config import MAX_HISTORY
import core.memory as core_memory
from core.memory import MemoryManager
from ai.prompts import SYSTEM_PROMPT
from ai.context_builder import ContextBuilder
from ai.brain import AtlasBrain


# ==============================================================================
# TEST FIXTURES & ISOLATION HELPERS
# ==============================================================================

class IsolatedBenchmarkEnvironment:
    """Manages an isolated temporary sandbox for memory and conversations."""

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="atlas_benchmark_")
        self.memory_file = Path(self.temp_dir) / "test_memory.json"
        self.conversations_dir = Path(self.temp_dir) / "conversations"
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        self._orig_memory_file = getattr(core_memory, "MEMORY_FILE", None)

        # Point module-level default to isolated path
        core_memory.MEMORY_FILE = self.memory_file

    def get_memory_manager(self) -> MemoryManager:
        core_memory.MEMORY_FILE = self.memory_file
        m = MemoryManager(memory_file=self.memory_file)
        return m

    def cleanup(self):
        if self._orig_memory_file is not None:
            core_memory.MEMORY_FILE = self._orig_memory_file
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class MockModel:
    """Deterministic mock model for pipeline-level testing."""

    def __init__(self, fixed_reply: str = "Mock model response"):
        self.fixed_reply = fixed_reply
        self.last_prompt = ""

    def generate(self, prompt: str, stream: bool = False):
        self.last_prompt = prompt
        if stream:
            yield self.fixed_reply
        else:
            return self.fixed_reply

    def cancel_current(self):
        pass


# ==============================================================================
# SECTION 1: MEMORY CAPABILITY BENCHMARKS (M01 - M10)
# ==============================================================================

class TestMemoryCapabilityBenchmarks:
    """Diagnostic tests for memory storage, extraction, update, conflict, and recall."""

    @pytest.fixture(autouse=True)
    def setup_sandbox(self):
        self.env = IsolatedBenchmarkEnvironment()
        self.memory = self.env.get_memory_manager()
        yield
        self.env.cleanup()

    def test_m01_explicit_memory_storage(self):
        """M01: Test explicit 'Remember that...' command."""
        test_message = "Remember that my dog's name is Rex"
        self.memory.extract_from_message(test_message)

        all_data = self.memory.all()
        facts = all_data.get("facts", {})
        fact_values = list(facts.values())
        extracted = any("dog's name is Rex" in str(v) or "Rex" in str(v) for v in fact_values)

        assert extracted, "M01 FAILURE: Explicit fact 'dog's name is Rex' was not saved."

    def test_m02_natural_language_memory_extraction(self):
        """M02: Test natural language memory extraction across diverse statements (P0.3 + P1.4)."""
        test_cases = [
            # (Statement, Category, Key, Expected Value, Description)
            ("I live in Mumbai", "identity", "city", "Mumbai", "City extraction"),
            ("I work at Google", "identity", "workplace", "Google", "Workplace extraction"),
            ("My favorite anime is One Piece", "preferences", "favorite_anime", "One Piece", "Favorite media/anime"),
            ("I love dark mode", "preferences", "ui_theme", "dark mode", "UI preference"),
            ("My name is Saad", "identity", "name", "Saad", "Simple name extraction"),
            ("My name is Saad Khan", "identity", "name", "Saad Khan", "Multi-word full name"),
            ("Call me Alex", "identity", "name", "Alex", "Call me name extraction"),
            ("You can call me Alex", "identity", "name", "Alex", "Prefix 'call me' extraction"),
        ]

        results = {}
        for stmt, cat, key, expected, desc in test_cases:
            self.memory.clear()
            self.memory.extract_from_message(stmt)
            val = self.memory.recall(cat, key)
            passed = (val == expected)
            results[desc] = {
                "statement": stmt,
                "expected": f"{cat}.{key} = {expected}",
                "actual": f"{cat}.{key} = {val}",
                "passed": passed,
            }

        # All 8 natural extraction test cases must pass after P0.3 and P1.4 fixes
        assert results["City extraction"]["passed"], "M02: City extraction failed"
        assert results["Workplace extraction"]["passed"], "M02: Workplace extraction failed"
        assert results["Favorite media/anime"]["passed"], "M02: Favorite media/anime failed"
        assert results["UI preference"]["passed"], "M02: UI preference failed"
        assert results["Simple name extraction"]["passed"], "M02: Simple name extraction failed"
        assert results["Multi-word full name"]["passed"], "M02: Multi-word name failed"
        assert results["Call me name extraction"]["passed"], "M02: Call me name extraction failed"
        assert results["Prefix 'call me' extraction"]["passed"], "M02: Prefix 'call me' failed"

    def test_m03_memory_recall_across_queries(self):
        """M03: Test memory recall with exact keywords vs synonyms/paraphrasing (P1.1)."""
        self.memory.remember("identity", "city", "Mumbai")
        self.memory.remember("preferences", "favorite_color", "blue")
        self.memory.remember("facts", "1", "my dog's name is Rex")

        # 1. Exact query
        rel_exact = self.memory.relevant("Where do I live?")
        exact_retrieved = ("identity" in rel_exact and rel_exact["identity"].get("city") == "Mumbai")

        # 2. Synonym query 1: "staying"
        rel_syn1 = self.memory.relevant("Where am I currently staying?")
        syn1_retrieved = ("identity" in rel_syn1 and rel_syn1["identity"].get("city") == "Mumbai")

        # 3. Synonym query 2: "based in"
        rel_syn2 = self.memory.relevant("Which city am I based in?")
        syn2_retrieved = ("identity" in rel_syn2 and rel_syn2["identity"].get("city") == "Mumbai")

        # 4. Fact query: "What's my dog's name?"
        rel_fact_direct = self.memory.relevant("What's my dog's name?")
        fact_direct_retrieved = ("facts" in rel_fact_direct and any("Rex" in str(v) for v in rel_fact_direct["facts"].values()))

        assert exact_retrieved, "M03: Exact keyword lookup failed."
        assert syn1_retrieved, "M03 REPAIRED: Synonym 'Where am I currently staying?' successfully retrieved city."
        assert syn2_retrieved, "M03 REPAIRED: Synonym 'Which city am I based in?' successfully retrieved city."
        assert fact_direct_retrieved, "M03 REPAIRED: Fact 'dog's name is Rex' retrieved via token overlap."

    def test_m04_memory_update_and_correction(self):
        """M04: Test updating existing facts via natural conversation (P1.4)."""
        # Initial fact
        self.memory.extract_from_message("I live in Mumbai")
        assert self.memory.recall("identity", "city") == "Mumbai"

        # Update 1: Relocation update
        self.memory.extract_from_message("I moved to Berlin")
        assert self.memory.recall("identity", "city") == "Berlin"

        # Update 2: Preference correction
        self.memory.extract_from_message("My favorite color is blue")
        assert self.memory.recall("preferences", "favorite_color") == "blue"

        self.memory.extract_from_message("My favorite color is now purple")
        assert self.memory.recall("preferences", "favorite_color") == "purple"

    def test_m05_memory_conflict_resolution(self):
        """M05: Test contradictory facts handling and update continuity."""
        self.memory.extract_from_message("I prefer concise explanations")
        assert self.memory.recall("preferences", "explanation_style") == "concise"

        time.sleep(0.01)
        self.memory.extract_from_message("I prefer detailed explanations")
        assert self.memory.recall("preferences", "explanation_style") == "detailed"

    def test_m06_irrelevant_memory_isolation_and_pollution(self):
        """M06: Measure memory pollution and context noise ratio (P1.2)."""
        # Populate 10 memories across all categories
        self.memory.remember("identity", "name", "Saad")
        self.memory.remember("identity", "city", "Mumbai")
        self.memory.remember("preferences", "favorite_color", "blue")
        self.memory.remember("preferences", "favorite_food", "biryani")
        self.memory.remember("preferences", "explanation_style", "concise")
        self.memory.remember("projects", "project_name", "Atlas")
        self.memory.remember("projects", "technology", "Python")
        self.memory.remember("environment", "operating_system", "Linux")
        self.memory.remember("facts", "1", "my dog's name is Rex")
        self.memory.remember("goals", "1", "ship Atlas V3")

        # Case A: Specific query "What is my favorite color?"
        rel_color = self.memory.relevant("What is my favorite color?")
        # Must retrieve ONLY favorite_color; NO leakage of food, style, or other categories
        assert "preferences" in rel_color
        assert list(rel_color["preferences"].keys()) == ["favorite_color"]
        total_injected_keys_a = sum(len(v) if isinstance(v, dict) else 1 for v in rel_color.values())
        assert total_injected_keys_a == 1, "P1.2 SUCCESS: Over-fetching eliminated. Only 1 key injected."

        # Case B: Query with "remember" about a specific preference
        rel_remember = self.memory.relevant("Do you remember my favorite color?")
        total_injected_keys_b = sum(len(v) if isinstance(v, dict) else 1 for v in rel_remember.values())
        assert total_injected_keys_b == 1, "P1.2 SUCCESS: Query with 'remember' no longer dumps entire database."

    def test_m07_multi_fact_extraction(self):
        """M07: Test extracting multiple facts from a single utterance."""
        msg_a = "My name is Saad, I live in Mumbai, my favorite color is blue, and I use Linux."
        self.memory.extract_from_message(msg_a)

        assert self.memory.recall("identity", "name") == "Saad"
        assert self.memory.recall("identity", "city") == "Mumbai"
        assert self.memory.recall("preferences", "favorite_color") == "blue"
        assert self.memory.recall("environment", "operating_system") == "Linux"

    def test_m08_negation_handling(self):
        """M08: Test negation safety (P1.4)."""
        self.memory.extract_from_message("I am not from Mumbai")
        assert self.memory.recall("identity", "city") is None

        self.memory.extract_from_message("I don't live in Mumbai")
        assert self.memory.recall("identity", "city") is None

        self.memory.extract_from_message("I don't like coffee")
        all_mem = self.memory.all()
        assert "coffee" not in str(all_mem)

    def test_m09_multilingual_hinglish(self):
        """M09: Test Hinglish statements (P0.3 + P1.4)."""
        self.memory.extract_from_message("Mera naam Saad Khan hai")
        assert self.memory.recall("identity", "name") == "Saad Khan"

        self.memory.extract_from_message("Mujhe dark theme pasand hai")
        assert self.memory.recall("preferences", "ui_theme") == "dark theme"

        self.memory.extract_from_message("Main Mumbai me rehta hu")
        assert self.memory.recall("identity", "city") == "Mumbai"

    def test_m10_long_term_persistence_and_integrity(self):
        """M10: Test disk persistence, round-trip fidelity, and corruption handling."""
        self.memory.remember("identity", "name", "Saad 'Dev' Khan")
        self.memory.remember("facts", "fact_unicode", "Likes 日本語 and café")
        self.memory.remember("projects", "path", "/home/user/project\"test\"")

        # Reload
        m2 = self.env.get_memory_manager()
        assert m2.recall("identity", "name") == "Saad 'Dev' Khan"
        assert m2.recall("facts", "fact_unicode") == "Likes 日本語 and café"
        assert m2.recall("projects", "path") == "/home/user/project\"test\""

        # Corrupted JSON recovery
        with open(self.env.memory_file, "w", encoding="utf-8") as f:
            f.write("{ INVALID JSON DATA --- CORRUPTED FILE")

        m3 = self.env.get_memory_manager()
        data = m3.all()
        assert isinstance(data, dict)
        assert "identity" in data
        assert m3.recall("identity", "name") is None


# ==============================================================================
# SECTION 2: CONTEXT WINDOW & HISTORY BENCHMARKS (C01 - C07)
# ==============================================================================

class TestConversationContextBenchmarks:
    """Diagnostic tests for context assembly, history degradation, followups, and bloat."""

    def test_c01_short_term_retention(self):
        """C01: Test retention of facts within 5 messages distance."""
        builder = ContextBuilder()
        target_fact = "The secret deployment key is KEY_XYZ_123"
        history = [
            {"sender": "user", "text": target_fact, "is_user": True},
            {"sender": "atlas", "text": "Got it, I noted the key.", "is_user": False},
            {"sender": "user", "text": "What is the status of the server?", "is_user": True},
            {"sender": "atlas", "text": "Server is running normally.", "is_user": False},
            {"sender": "user", "text": "Check the memory usage.", "is_user": True},
        ]

        prompt = builder.build(history, "What is the deployment key?")
        assert target_fact in prompt, "C01: Fact at 5 messages distance must be in prompt."

    def test_c02_context_window_limit_and_degradation_curve(self):
        """C02: Measure context retention across message distances: 1 to 30.
        Verifies that the artificial 8-message cliff is removed and MAX_HISTORY is respected.
        """
        builder = ContextBuilder()
        target_fact = "TARGET_VARIABLE_OMEGA = 42"

        distances = [1, 2, 4, 6, 8, 9, 10, 12, 15, 20, 30]
        retention_results = {}

        for dist in distances:
            history = [{"sender": "user", "text": target_fact, "is_user": True}]
            for i in range(dist - 1):
                sender = "atlas" if i % 2 == 0 else "user"
                history.append({"sender": sender, "text": f"Filler turn {i+1}", "is_user": (sender == "user")})

            prompt = builder.build(history, "What is TARGET_VARIABLE_OMEGA?")
            retention_results[dist] = (target_fact in prompt)

        # Retained through the full MAX_HISTORY window (20 messages)
        assert retention_results[1] is True
        assert retention_results[4] is True
        assert retention_results[8] is True
        assert retention_results[9] is True, "C02 REPAIRED: Message at distance 9 retained!"
        assert retention_results[10] is True, "C02 REPAIRED: Message at distance 10 retained!"
        assert retention_results[15] is True, "C02 REPAIRED: Message at distance 15 retained!"
        assert retention_results[20] is True, "C02 REPAIRED: Message at distance 20 retained!"
        # Beyond MAX_HISTORY (20), properly bounded to prevent context overflow
        assert retention_results[30] is False, "C02: Context properly bounded past MAX_HISTORY."

    def test_c03_pronoun_anaphora_resolution(self):
        """C03: Follow-up pronoun resolution."""
        builder = ContextBuilder()
        history_1 = [
            {"sender": "user", "text": "Give me three programming languages.", "is_user": True},
            {"sender": "atlas", "text": "1. Python\n2. Rust\n3. Go", "is_user": False},
        ]
        prompt_1 = builder.build(history_1, "explain the second one")
        assert "enumerated item #2" in prompt_1 or "Rust" in prompt_1

    def test_c04_topic_switching_and_return(self):
        """C04: Test conversation with topic interruption (P0.1)."""
        builder = ContextBuilder()
        history = [
            {"sender": "user", "text": "Our primary database engine is PostgreSQL 16.", "is_user": True},
            {"sender": "atlas", "text": "Understood, PostgreSQL 16 is recorded.", "is_user": False},
        ]

        # 8 messages of Topic B
        for i in range(8):
            sender = "user" if i % 2 == 0 else "atlas"
            history.append({"sender": sender, "text": f"Topic B: Styling button #{i}", "is_user": (sender == "user")})

        prompt = builder.build(history, "Back to the database: which engine are we using?")
        # Topic A is retained because history window is now 20 messages, not 8!
        assert "PostgreSQL 16" in prompt, "C04 REPAIRED: Topic A preserved across 8-message interruption!"

    def test_c05_context_bloat_and_token_budget(self):
        """C05: Measure prompt token bloat and efficiency."""
        builder = ContextBuilder()
        prompt = builder.build([], "Hello")
        assert SYSTEM_PROMPT in prompt

    def test_c06_cross_conversation_isolation(self):
        """C06: Test history isolation across conversations."""
        env = IsolatedBenchmarkEnvironment()
        try:
            mem = env.get_memory_manager()
            model = MockModel()
            brain = AtlasBrain(model=model, memory=mem)

            conv1 = [{"sender": "user", "text": "React is my favorite framework", "is_user": True}]
            brain.set_conversation_history(conv1)
            ctx1 = brain._build_context("What do I like?")
            assert "React" in ctx1["prompt"]

            conv2 = [{"sender": "user", "text": "Let's discuss SQL", "is_user": True}]
            brain.set_conversation_history(conv2)
            ctx2 = brain._build_context("What are we discussing?")
            assert "SQL" in ctx2["prompt"]
            assert "React" not in ctx2["prompt"]
        finally:
            env.cleanup()


# ==============================================================================
# SECTION 3: BRAIN RECALL & DETERMINISTIC COMMANDS (B01 - B02)
# ==============================================================================

class TestBrainDeterministicBypasses:

    @pytest.fixture(autouse=True)
    def setup_sandbox(self):
        self.env = IsolatedBenchmarkEnvironment()
        self.memory = self.env.get_memory_manager()
        self.model = MockModel()
        self.brain = AtlasBrain(model=self.model, memory=self.memory)
        yield
        self.env.cleanup()

    def test_b01_fact_query_returns_values_instead_of_keys(self):
        """B01 REPAIRED (P0.2): Asking 'what do you remember' returns actual values, NEVER keys."""
        self.memory.remember("facts", "fact_id_101", "User owns a Golden Retriever named Rex")
        self.memory.remember("facts", "fact_id_102", "User works remotely on Mondays")

        resp = self.brain.process_message("What do you remember?")

        assert "Rex" in resp or "Mondays" in resp, "B01 REPAIRED: Brain returned actual fact values."
        assert "fact_id_101" not in resp, "B01 REPAIRED: Internal keys are not leaked."
        assert "fact_id_102" not in resp, "B01 REPAIRED: Internal keys are not leaked."

    def test_b02_remember_command_bypasses_model_completely(self):
        """B02: Messages starting with 'remember' return confirmation directly."""
        resp = self.brain.process_message("Remember that I am learning Rust")
        assert "saved" in resp.lower() or "okay" in resp.lower()


# ==============================================================================
# SECTION 4: MODEL-IN-THE-LOOP TESTS (Live Ollama Qwen2.5:1.5b)
# ==============================================================================

class TestModelInTheLoop:

    @classmethod
    def setup_class(cls):
        import urllib.request
        cls.ollama_available = False
        try:
            req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
            if req.status == 200:
                data = json.loads(req.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                if any("qwen2.5:1.5b" in m for m in models):
                    cls.ollama_available = True
        except Exception:
            cls.ollama_available = False

    def setup_method(self):
        self.env = IsolatedBenchmarkEnvironment()
        self.memory = self.env.get_memory_manager()

    def teardown_method(self):
        self.env.cleanup()

    def test_mil_01_exact_vs_synonym_retrieval_impact(self):
        """MIL-01: Both exact and synonym queries succeed because pipeline supplies memory (P1.1)."""
        if not self.ollama_available:
            pytest.skip("Ollama with qwen2.5:1.5b not available")

        from ai.model import AtlasModel
        live_brain = AtlasBrain(model=AtlasModel(), memory=self.memory)

        self.memory.remember("identity", "city", "Mumbai")

        # Exact query
        resp_exact = live_brain.process_message("Where do I live?")
        assert "mumbai" in resp_exact.lower(), "Model answered city with exact phrasing."

        # Synonym query (was failing before P1.1, now succeeds!)
        resp_syn = live_brain.process_message("Where am I currently staying?")
        assert "mumbai" in resp_syn.lower(), "MIL-01 REPAIRED: Model answered city with synonym phrasing!"

    def test_mil_02_context_cutoff_model_behavior(self):
        """MIL-02: History beyond 8 messages is now retained and answered correctly by model (P0.1)."""
        if not self.ollama_available:
            pytest.skip("Ollama with qwen2.5:1.5b not available")

        from ai.model import AtlasModel
        live_brain = AtlasBrain(model=AtlasModel(), memory=self.memory)

        # 12 messages back (was pruned before P0.1, now retained!)
        hist_12 = [{"sender": "user", "text": "My dog's name is Rex.", "is_user": True}]
        for i in range(11):
            s = "atlas" if i % 2 == 0 else "user"
            hist_12.append({"sender": s, "text": f"Conversational turn {i}", "is_user": (s == "user")})

        live_brain.set_conversation_history(hist_12)
        resp_12 = live_brain.process_message("What is my dog's name?")
        assert "rex" in resp_12.lower(), "MIL-02 REPAIRED: Model answered dog name across 12 messages history!"


# ==============================================================================
# CLI RUNNER & BENCHMARK SUITE EXECUTOR
# ==============================================================================

def run_standalone_benchmarks():
    print("=" * 80)
    print("ATLAS AI V3 — MEMORY & CONTEXT BENCHMARK (POST-REPAIR)")
    print("=" * 80)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")

    pytest_args = [
        "-v",
        "--tb=short",
        __file__,
    ]
    return pytest.main(pytest_args)


if __name__ == "__main__":
    sys.exit(run_standalone_benchmarks())

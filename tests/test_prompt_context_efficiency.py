"""
Tests for Prompt and Context Efficiency (AtlasAI V3)
Verifies:
1. immediate follow-up
2. multi-turn context
3. old irrelevant conversation
4. memory-based recall
5. correction of an existing fact
6. current message not duplicated
"""
import pytest
from ai.context_builder import ContextBuilder
from core.memory import MemoryManager

def make_msg(sender, text, is_user=False):
    return {"sender": sender, "text": text, "is_user": is_user}

def test_immediate_followup():
    cb = ContextBuilder()
    history = [
        make_msg("User", "What is the capital of France?", True),
        make_msg("Atlas", "The capital of France is Paris."),
    ]
    prompt = cb.build(history, "What is its population?")
    assert "FOLLOW-UP CLARIFICATION" in prompt or "Paris" in prompt
    assert "What is its population?" in prompt

def test_multiturn_context():
    cb = ContextBuilder(max_history=10)
    history = [
        make_msg("User", f"Step {i}", True) if i % 2 == 0 else make_msg("Atlas", f"Response {i}")
        for i in range(8)
    ]
    prompt = cb.build(history, "What is the next step?")
    assert "Step 0" in prompt
    assert "Step 6" in prompt
    assert "What is the next step?" in prompt

def test_old_irrelevant_conversation():
    cb = ContextBuilder(max_history=6)
    history = [
        make_msg("User", f"Old message {i}", True) if i % 2 == 0 else make_msg("Atlas", f"Old response {i}")
        for i in range(20)
    ]
    prompt = cb.build(history, "Current task")
    # Oldest messages should be pruned
    assert "Old message 0" not in prompt
    assert "Old message 2" not in prompt
    # Recent messages within max_history=6 should be retained
    assert "Old message 18" in prompt
    assert "Current task" in prompt

def test_memory_based_recall(tmp_path):
    mem_file = tmp_path / "test_mem.json"
    mem = MemoryManager(memory_file=mem_file)
    mem.remember("identity", "name", "Saad")
    mem.remember("projects", "project_name", "TheOtherSide")

    cb = ContextBuilder()
    relevant = mem.relevant("What game am I developing?")
    assert "TheOtherSide" in str(relevant)

    prompt = cb.build([], "What game am I developing?", memory=relevant)
    assert "===== RELEVANT PERSISTENT MEMORY =====" in prompt
    assert "TheOtherSide" in prompt

def test_correction_of_existing_fact(tmp_path):
    mem_file = tmp_path / "test_mem.json"
    mem = MemoryManager(memory_file=mem_file)
    mem.extract_from_message("I live in Mumbai")
    assert mem.recall("identity", "city") == "Mumbai"

    # User corrects their location
    mem.extract_from_message("I moved to Berlin")
    assert mem.recall("identity", "city") == "Berlin"

    cb = ContextBuilder()
    relevant = mem.relevant("Where do I live?")
    prompt = cb.build([], "Where do I live?", memory=relevant)
    assert "Berlin" in prompt
    assert "Mumbai" not in prompt

def test_current_message_not_duplicated():
    cb = ContextBuilder()
    # History already appended the current message prior to prompt building
    history = [
        make_msg("User", "Hello Atlas", True),
        make_msg("Atlas", "Hello! How can I help?"),
        make_msg("User", "Why is water wet?", True),
    ]
    prompt = cb.build(history, "Why is water wet?")

    # "Why is water wet?" should be in CURRENT USER MESSAGE, NOT duplicated in RECENT CONVERSATION
    assert "===== CURRENT USER MESSAGE =====\nUser: Why is water wet?" in prompt
    recent_part = prompt.split("===== RECENT CONVERSATION =====")[1].split("===== END RECENT CONVERSATION =====")[0]
    assert "Why is water wet?" not in recent_part
    assert "Hello Atlas" in recent_part

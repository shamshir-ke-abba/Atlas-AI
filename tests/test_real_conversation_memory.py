"""Regression test for real-world conversation memory and context lifecycle.

Specifically verifies the failure reported in conversation 47e9ef2d-682d-40f5-97d4-85b80546fe69:
- Fact extraction of "Im working on a game called TheOtherSIde" (including without apostrophe)
- Relevance retrieval of ("projects", "project_name") for game-related queries
- Multi-turn conversation history synchronization and prompt building
"""

import tempfile
from pathlib import Path
import pytest

from core.memory import MemoryManager
from ai.brain import AtlasBrain
from ai.context_builder import ContextBuilder


def test_game_project_extraction_and_relevance():
    with tempfile.NamedTemporaryFile(suffix=".json") as f:
        mem = MemoryManager(memory_file=f.name)

        # 1. Fact extraction: un-apostrophized "Im" with game called
        mem.extract_from_message("Im working on a game called TheOtherSIde")
        assert mem.recall("projects", "project_name") == "TheOtherSIde"

        # 2. Relevance retrieval for "What is the name of the game im working on?"
        rel1 = mem.relevant("What is the name of the game im working on?")
        assert "projects" in rel1
        assert rel1["projects"].get("project_name") == "TheOtherSIde"

        # 3. Relevance retrieval for "what game am i working on?"
        rel2 = mem.relevant("what game am i working on?")
        assert "projects" in rel2
        assert rel2["projects"].get("project_name") == "TheOtherSIde"

        # 4. Quoted game extraction: "Im working on a game called \"TheOtherSide\""
        mem.clear()
        mem.extract_from_message('Im working on a game called "TheOtherSide"')
        assert mem.recall("projects", "project_name") == "TheOtherSide"


def test_multi_turn_conversation_context_in_prompt():
    with tempfile.NamedTemporaryFile(suffix=".json") as f:
        mem = MemoryManager(memory_file=f.name)
        mem.extract_from_message("Im working on a game called TheOtherSIde")

        builder = ContextBuilder(max_history=10)
        history = [
            {"sender": "User", "text": "Im working on a game called TheOtherSIde", "is_user": True},
            {"sender": "Atlas", "text": 'Hello! Working on "TheOtherSide" sounds exciting.', "is_user": False},
            {"sender": "User", "text": "Its a psychological horror game", "is_user": True},
            {"sender": "Atlas", "text": "That sounds intriguing!", "is_user": False},
        ]

        query = "What is the name of the game im working on?"
        relevant_mem = mem.relevant(query)

        prompt = builder.build(
            conversation_history=history,
            current_message=query,
            memory=relevant_mem,
        )

        # Prompt must contain persistent memory
        assert "TheOtherSIde" in prompt
        assert "===== RELEVANT PERSISTENT MEMORY =====" in prompt

        # Prompt must contain prior conversation history
        assert "===== RECENT CONVERSATION =====" in prompt
        assert "User: Im working on a game called TheOtherSIde" in prompt
        assert 'Atlas: Hello! Working on "TheOtherSide" sounds exciting.' in prompt
        assert "User: Its a psychological horror game" in prompt

        # Prompt must contain current message
        assert "===== CURRENT USER MESSAGE =====" in prompt
        assert f"User: {query}" in prompt


def test_context_builder_deduplicates_current_user_message():
    builder = ContextBuilder(max_history=10)
    history = [
        {"sender": "User", "text": "Turn 1", "is_user": True},
        {"sender": "Atlas", "text": "Response 1", "is_user": False},
        {"sender": "User", "text": "Turn 2", "is_user": True},
    ]

    prompt = builder.build(
        conversation_history=history,
        current_message="Turn 2",
    )

    # "Turn 2" should be in CURRENT USER MESSAGE, but NOT duplicated in RECENT CONVERSATION
    recent_section = prompt.split("===== RECENT CONVERSATION =====")[1].split("===== END RECENT CONVERSATION =====")[0]
    assert "User: Turn 1" in recent_section
    assert "Atlas: Response 1" in recent_section
    assert "Turn 2" not in recent_section
    assert "===== CURRENT USER MESSAGE =====\nUser: Turn 2" in prompt

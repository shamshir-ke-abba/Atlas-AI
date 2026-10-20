"""Regression tests for Prompt Echoing in the Coder AI / Atlas AI assistant.

Verifies:
- Test A: Basic instruction following (Python function generation, no prompt echo)
- Test B: Multi-file task (portfolio website with HTML, CSS, JS filenames)
- Test C: Prompt echo detection (summary generation, verifying input != output)
- Test D: Streaming output verification (token ordering, no input prompt duplication)
- Test E: Failure handling (empty response and API failure report errors, no prompt substitution)
- Test F: Conversation continuity (multi-turn follow-up uses history, does not echo full conversation)
- Benchmark regression: Large structured task with 'VS Code' and 'current' does not get hijacked by web_search.
"""

from typing import Generator, List
from unittest.mock import MagicMock, patch
import pytest

from ai.brain import AtlasBrain
from ai.context_builder import ContextBuilder
from core.tool_manager import ToolManager
from plugins.system.web_search import WebSearchPlugin


class MockStreamingModel:
    """Mock model providing controllable token streaming for deterministic testing."""

    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.prompts_received = []
        self._cancelled = False

    def generate(self, prompt: str, stream: bool = True) -> Generator[str, None, None]:
        self.prompts_received.append(prompt)
        if not self.responses:
            return
        resp = self.responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        # Yield in realistic word/chunk tokens
        for token in resp.split(" "):
            yield token + " "

    def is_available(self) -> bool:
        return True


# =====================================================================
# Test A — Basic instruction following
# =====================================================================

def test_a_basic_instruction_following():
    """Input: 'Write a Python function that adds two numbers.'
    Expected: A Python function that adds two numbers, not a reproduction of the request.
    """
    tools = ToolManager()
    brain = AtlasBrain(tools=tools)

    user_input = "Write a Python function that adds two numbers."

    # Verify tool matching does not hijack this coding task
    matched_tool = tools.match(user_input)
    assert matched_tool is None or getattr(matched_tool, "name", "") != "web_search", (
        "Coding instruction must not be hijacked by web_search"
    )

    chunks = list(brain.stream_message(user_input))
    response = "".join(chunks).strip()

    # Must contain a function implementation
    assert "def " in response, f"Expected function definition in response, got: {response}"
    assert "return " in response or "+" in response, f"Expected function body in response, got: {response}"

    # Must not be an echo of the prompt
    assert response != user_input, "Model must not output the original prompt verbatim"
    assert not response.startswith(user_input), "Model output must not start with the raw user prompt"
    assert "I searched the web for" not in response, "Should not produce search fallback message"


# =====================================================================
# Test B — Multi-file task
# =====================================================================

def test_b_multi_file_task():
    """Input: 'Design a portfolio website with separate HTML, CSS, and JavaScript files. Explain the exact filename for each file.'
    Expected: A useful implementation response with file-specific content, not the original instruction.
    """
    tools = ToolManager()
    brain = AtlasBrain(tools=tools)

    user_input = (
        "Design a portfolio website with separate HTML, CSS, and JavaScript files in VS Code. "
        "Explain the exact filename for each file."
    )

    # Verify 'in VS Code' does not trigger web search
    matched_tool = tools.match(user_input)
    assert matched_tool is None or getattr(matched_tool, "name", "") != "web_search", (
        "Task mentioning VS Code must not be hijacked by web_search"
    )

    chunks = list(brain.stream_message(user_input))
    response = "".join(chunks).strip()

    # Must contain file-specific guidance
    response_lower = response.lower()
    assert ".html" in response_lower, "Response must specify HTML filename"
    assert ".css" in response_lower, "Response must specify CSS filename"
    assert ".js" in response_lower, "Response must specify JS filename"

    # Must not echo prompt
    assert response != user_input, "Model must not output the original prompt verbatim"
    assert "I searched the web for" not in response


# =====================================================================
# Test C — Prompt echo detection
# =====================================================================

def test_c_prompt_echo_detection():
    """Input: 'Summarize why testing is important in software development.'
    Expected: A relevant summary. Verify that the system does not mistakenly treat the input message as the generated output.
    """
    tools = ToolManager()
    brain = AtlasBrain(tools=tools)

    user_input = "Summarize why testing is important in software development."

    chunks = list(brain.stream_message(user_input))
    response = "".join(chunks).strip()

    assert response != user_input, "System mistakenly treated input message as generated output"
    assert len(response) > len(user_input) // 2
    assert not response.strip().startswith(user_input), "Response should not just repeat the user's prompt"

    # Verify context builder prompt structure
    builder = ContextBuilder()
    built = builder.build([], user_input)
    assert f"User: {user_input}" in built
    assert "Atlas:" in built
    assert "NEVER echo, repeat, or quote the user's prompt" in built


# =====================================================================
# Test D — Streaming
# =====================================================================

def test_d_streaming_order_and_content():
    """Verify that streamed output contains generated response tokens in the correct order
    and does not duplicate the user's submitted prompt as assistant content.
    """
    expected_tokens = ["def ", "add(a, ", "b):\n    ", "return ", "a + b\n"]
    mock_model = MockStreamingModel(responses=["".join(expected_tokens)])

    tools = ToolManager()
    brain = AtlasBrain(model=mock_model, tools=tools)

    user_input = "Write a Python function that adds two numbers."
    streamed_chunks = []
    for chunk in brain.stream_message(user_input):
        streamed_chunks.append(chunk)

    assembled = "".join(streamed_chunks).strip()
    assert "def add(a, b):" in assembled
    assert "return a + b" in assembled

    # Verify user prompt is NOT streamed as assistant content
    for chunk in streamed_chunks:
        assert chunk.strip() != user_input, "Streamed chunk must not contain the entire user prompt"

    assert user_input not in assembled, "Assembled streamed response must not duplicate the input prompt"


# =====================================================================
# Test E — Failure handling
# =====================================================================

def test_e_empty_response_failure_handling():
    """Simulate an empty model response.
    Verify that the application reports the failure rather than presenting the original prompt as the answer.
    """
    mock_model = MockStreamingModel(responses=[""])  # Empty string from model

    tools = ToolManager()
    brain = AtlasBrain(model=mock_model, tools=tools)

    user_input = "Write a Python function to solve fizzbuzz."
    chunks = list(brain.stream_message(user_input))
    response = "".join(chunks).strip()

    assert response == "No response generated.", (
        f"Expected explicit empty response indicator, got: {response}"
    )
    assert response != user_input, "Must not silently substitute original prompt for empty response"


def test_e_api_failure_handling():
    """Simulate an API failure / ConnectionError.
    Verify that the application reports the failure rather than presenting the original prompt as the answer.
    """
    mock_model = MockStreamingModel(responses=[RuntimeError("Connection refused: Ollama unreachable")])

    tools = ToolManager()
    brain = AtlasBrain(model=mock_model, tools=tools)

    user_input = "Write a function to invert a binary tree."
    chunks = list(brain.stream_message(user_input))
    response = "".join(chunks).strip()

    assert response.startswith("Error:"), (
        f"Expected error report starting with 'Error:', got: {response}"
    )
    assert "Connection refused" in response or "Ollama" in response
    assert response != user_input, "Must not substitute original prompt on API failure"


def test_e_web_search_failure_falls_back_to_model():
    """Simulate web search returning no results.
    Verify that the system falls back to the model rather than echoing the query in a failure message.
    """
    mock_model = MockStreamingModel(responses=["Model fallback answer based on internal knowledge."])
    plugin = WebSearchPlugin()

    # Simulate web search returning no evidence
    with patch.object(plugin, "can_handle", return_value=True), \
         patch.object(plugin, "research", return_value=MagicMock(has_evidence=False)), \
         patch.object(plugin, "search_results", return_value=[]):

        tools = MagicMock()
        tools.match.return_value = plugin
        brain = AtlasBrain(model=mock_model, tools=tools)

        user_input = "What is the latest release date of Python 3.14?"
        chunks = list(brain.stream_message(user_input))
        response = "".join(chunks).strip()

        assert "Model fallback answer" in response
        assert "I searched the web for" not in response, "Must not return dead-end echoed prompt"
        assert response != user_input


# =====================================================================
# Test F — Conversation continuity
# =====================================================================

def test_f_conversation_continuity():
    """Send a follow-up question and verify that the model uses relevant history
    without reproducing the full conversation as its answer.
    """
    history = [
        {"sender": "User", "text": "I am working on an arcade game in Python.", "is_user": True},
        {"sender": "Atlas", "text": "That sounds fun! What library are you using?", "is_user": False},
        {"sender": "User", "text": "I am using Pygame.", "is_user": True},
        {"sender": "Atlas", "text": "Pygame is great for 2D arcade games.", "is_user": False},
    ]

    tools = ToolManager()
    brain = AtlasBrain(tools=tools)

    follow_up = "What library did I say I am using?"
    chunks = list(brain.stream_message(follow_up, conversation_history=history))
    response = "".join(chunks).strip()

    # Model should mention Pygame from history
    assert "pygame" in response.lower(), f"Expected response to mention Pygame from history, got: {response}"

    # Must not reproduce the entire conversation transcript as the output
    assert "User: I am working on an arcade game in Python." not in response
    assert "Atlas: That sounds fun!" not in response
    assert response != follow_up, "Must not echo follow-up prompt"


# =====================================================================
# Benchmark Regression — Saad's Portfolio task
# =====================================================================

def test_benchmark_portfolio_task_not_hijacked():
    """Verify that a large multi-paragraph portfolio task containing 'VS Code' and 'current'
    is NOT classified as a web search and does not echo back.
    """
    benchmark_task = """# BENCHMARK TASK: BUILD SAAD'S DEVELOPER PORTFOLIO

## CRITICAL EXECUTION CONSTRAINT
You currently do not have the ability to read, create, edit, or save files directly on my computer.
Therefore, you MUST deliver the entire project through your response using complete, copy-paste-ready code blocks.

### Mandatory file-generation protocol
FILE 1 — `index.html`
FILE 2 — `css/style.css`
FILE 3 — `js/main.js`

## PROJECTS TO SHOWCASE
### 1. Arclune — Music Platform
Offline-first Android music player.

### 2. Aster — Private Messaging Application
Real-time WebSocket messaging platform.

### 3. Aetherbound — Creature-Bonding RPG
Its current prototype focuses on movement and exploration.

At the end, provide exact instructions to assemble and run the project in VS Code.
"""
    plugin = WebSearchPlugin()
    assert plugin.can_handle(benchmark_task) is False, (
        "WebSearchPlugin must not claim to handle multi-line coding task containing 'VS Code' or 'current'"
    )

    tools = ToolManager()
    assert tools.match(benchmark_task) is None, (
        "ToolManager must route benchmark coding task to the model, not a tool"
    )

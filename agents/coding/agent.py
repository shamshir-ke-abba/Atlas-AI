"""Atlas Coding Agent

Autonomous software engineering agent for local codebase inspection,
file modification, test execution, and multi-step coding workflows.
"""

import json
from pathlib import Path
import re
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

from agents.coding.context import RepositoryContext
from agents.coding.model import CodingModel
from agents.coding.permissions import CodingPermissions
from agents.coding.planner import CodingPlanner
from agents.coding.change_generator import CodingChangeGenerator
from agents.coding.tools.filesystem import CodeFilesystem
from core.logger import logger


CODING_AGENT_SYSTEM_PROMPT = """You are Atlas Coding Agent, an autonomous software engineering assistant.
Permitted workspace: {workspace}

AVAILABLE TOOLS:
- list_files(path="."): List files and directories in workspace.
- read_file(path): Read file contents.
- write_file(path, content): Create a file or overwrite an existing file with content.
- edit_file(path, old_text, new_text): Replace exact old_text with new_text in an existing file.
- search_files(query, path="."): Search workspace files for text.
- create_directory(path): Create directory in workspace.
- get_absolute_path(path): Return the absolute path of a file.
- run_tests(test_path=None): Run pytest on workspace or a specific test file.

PROTOCOL:
To execute a tool, output:
ACTION: <tool_name>
ARGUMENTS: <json_arguments>

When all operations are finished, output:
FINAL_ANSWER: <your comprehensive answer reporting all operations, read contents, and absolute paths>

RULES:
1. Actually perform every operation step-by-step using tools. Do NOT print shell scripts or markdown code blocks instead of using tools.
2. Complete every single requested step in order.
3. Steps asking to "Report", "Show", or "List" findings to the user are to be answered in your FINAL_ANSWER.
4. Once all requested file operations are completed, conclude immediately with FINAL_ANSWER.
5. In write_file and edit_file, use the exact verbatim content requested by the user, preserving exact characters and dashes.

EXAMPLES:
User: List the files in the directory.
Atlas:
ACTION: list_files
ARGUMENTS: {{"path": "."}}

User: Create a file named atlas_fs_test.txt containing exactly Initial content.
Atlas:
ACTION: write_file
ARGUMENTS: {{"path": "atlas_fs_test.txt", "content": "Initial content"}}

User: Read the file and show its exact contents.
Atlas:
ACTION: read_file
ARGUMENTS: {{"path": "atlas_fs_test.txt"}}

User: Modify the file so it contains exactly Initial content — modified successfully.
Atlas:
ACTION: edit_file
ARGUMENTS: {{"path": "atlas_fs_test.txt", "old_text": "Initial content", "new_text": "Initial content — modified successfully"}}

User: Report the absolute path of the file.
Atlas:
ACTION: get_absolute_path
ARGUMENTS: {{"path": "atlas_fs_test.txt"}}
"""


class CodingAgent:
    """Autonomous software engineering agent for Atlas V3."""

    def __init__(
        self,
        workspace: Optional[Union[str, Path]] = None,
        model: Optional[CodingModel] = None,
        permissions: Optional[CodingPermissions] = None,
    ):
        self.workspace = Path(workspace or Path.cwd()).resolve()
        self.model = model or CodingModel()
        self.permissions = (
            permissions
            if permissions is not None
            else CodingPermissions(allow_write=True, allow_tests=True)
        )

        self.fs = CodeFilesystem(
            workspace=self.workspace,
            allow_write=self.permissions.allow_write,
            allow_tests=self.permissions.allow_tests,
        )

        self.context = RepositoryContext(self.workspace)
        self.planner = CodingPlanner(model=self.model)
        self.change_generator = CodingChangeGenerator(model=self.model)

    # ======================================================
    # REPOSITORY INSPECTION & PLANNING (BACKWARD COMPATIBILITY)
    # ======================================================

    def inspect(self, task: str) -> str:
        """Build focused repository context for a coding task."""
        files = self.context.list_files(max_files=500)
        target_paths = self._extract_paths(task, files)
        search_terms = self._extract_search_terms(task)

        relevant_files = []
        for path in target_paths:
            if path not in relevant_files:
                relevant_files.append(path)

        for term in search_terms:
            matches = self.context.search(term, max_results=20)
            for match in matches:
                file_path = match["file"]
                if file_path not in relevant_files:
                    relevant_files.append(file_path)

        relevant_files = relevant_files[:50]
        file_list = "\n".join(f"- {path}" for path in files)

        search_results = []
        for term in search_terms:
            matches = self.context.search(term, max_results=20)
            for match in matches:
                if match not in search_results:
                    search_results.append(match)

        formatted_results = "\n".join(
            f"- {item['file']}:{item['line']} {item['text']}"
            for item in search_results[:50]
        )

        relevant_file_list = "\n".join(f"- {path}" for path in relevant_files)

        return f"""
PROJECT FILES:
{file_list or "No files found."}

PRIMARY TARGETS:
{relevant_file_list or "No explicit targets found."}

SEARCH RESULTS:
{formatted_results or "No relevant matches found."}
""".strip()

    @staticmethod
    def _extract_paths(task: str, files: List[str]) -> List[str]:
        text = str(task or "")
        found = []
        for file_path in files:
            if file_path in text:
                found.append(file_path)

        path_patterns = re.findall(
            r"(?:^|[\s`'\"(])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+(?:\.[A-Za-z0-9_+-]+)?)",
            text,
        )
        for path in path_patterns:
            normalized = path.strip(".,!?;:)]}")
            if normalized in files and normalized not in found:
                found.append(normalized)
        return found

    @staticmethod
    def _extract_search_terms(task: str) -> List[str]:
        words = str(task or "").split()
        stop_words = {
            "the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or",
            "is", "it", "this", "that", "please", "can", "you", "me", "fix",
            "change", "modify", "update", "add", "implement", "create", "remove",
            "bug", "error", "issue", "problem",
        }
        terms = []
        for word in words:
            cleaned = word.strip(".,!?;:()[]{}\"'`")
            if (
                len(cleaned) >= 3
                and cleaned.lower() not in stop_words
                and cleaned not in terms
                and "/" not in cleaned
            ):
                terms.append(cleaned)
        return terms[:8]

    def plan(self, task: str):
        """Create a structured plan from repository context."""
        repository_context = self.inspect(task)
        return self.planner.create_plan(task, repository_context)

    def generate_changes(self, task: str, plan=None):
        """Generate structured code changes without modifying files."""
        if plan is None:
            plan = self.plan(task)
        repository_context = self.inspect(task)
        return self.change_generator.generate(task, plan, repository_context)

    def build_prompt(self, task: str) -> str:
        from agents.coding.prompts import CODING_SYSTEM_PROMPT
        context = self.inspect(task)
        return f"""
{CODING_SYSTEM_PROMPT}

WORKSPACE:
{self.workspace}

USER TASK:
{task}

REPOSITORY CONTEXT:
{context}

Based ONLY on the repository information available above:
1. Identify the most relevant files.
2. Explain what should be inspected next.
3. Explain your proposed change.
4. Do not claim that you changed anything.
5. Do not invent files or code.
""".strip()

    def execute(
        self,
        task: str,
        permissions: Optional[CodingPermissions] = None,
        max_attempts: int = 2,
    ):
        """Execute a coding task through the workflow (for workflow test compatibility)."""
        task = str(task or "").strip()
        if not task:
            return "Coding task is empty."

        if not self.model.is_available():
            return (
                f"Coding model '{self.model.model_name}' "
                "is not available in Ollama."
            )

        if permissions is None:
            from agents.coding.permission_manager import CodingPermissionManager
            permission_manager = CodingPermissionManager()
            permissions = permission_manager.permissions()

        from agents.coding.workflow import CodingWorkflow
        workflow = CodingWorkflow(
            agent=self,
            permissions=permissions,
            max_attempts=max_attempts,
        )
        return workflow.run(task)

    # ======================================================
    # DIRECT TOOL EXECUTION
    # ======================================================

    def normalize_args(self, action: str, raw_args: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize argument keys for tool methods."""
        norm = dict(raw_args or {})

        # Path alias normalization
        if "path" not in norm:
            for k in (
                "file",
                "filename",
                "filepath",
                "file_path",
                "target",
                "dir",
                "directory",
                "directory_name",
            ):
                if k in norm:
                    norm["path"] = norm[k]
                    break

        # Content alias normalization
        if "content" not in norm:
            for k in ("text", "data", "body"):
                if k in norm:
                    norm["content"] = norm[k]
                    break

        # Old text normalization
        if "old_text" not in norm:
            for k in ("old", "find", "search", "old_content", "target_text"):
                if k in norm:
                    norm["old_text"] = norm[k]
                    break

        # New text normalization
        if "new_text" not in norm:
            for k in ("new", "replace", "new_content", "replacement"):
                if k in norm:
                    norm["new_text"] = norm[k]
                    break

        # Query alias normalization
        if "query" not in norm:
            for k in ("search", "pattern", "q", "text"):
                if k in norm:
                    norm["query"] = norm[k]
                    break

        # Test path alias normalization
        if "test_path" not in norm:
            for k in ("test", "tests", "path", "target"):
                if k in norm and norm[k]:
                    norm["test_path"] = norm[k]
                    break

        return norm

    def execute_tool(self, action: str, raw_args: Dict[str, Any]) -> Any:
        """Execute a named tool within the permitted workspace."""
        action = str(action or "").strip().lower()
        args = self.normalize_args(action, raw_args)

        tool_map = {
            "list_files": lambda: self.fs.list_files(args.get("path", ".")),
            "read_file": lambda: self.fs.read_file(args.get("path", "")),
            "write_file": lambda: self.fs.write_file(
                args.get("path", ""),
                args.get("content", ""),
            ),
            "create_file": lambda: self.fs.write_file(
                args.get("path", ""),
                args.get("content", ""),
            ),
            "edit_file": lambda: self.fs.edit_file(
                args.get("path", ""),
                old_text=args.get("old_text"),
                new_text=args.get("new_text", ""),
            ),
            "modify_file": lambda: self.fs.edit_file(
                args.get("path", ""),
                old_text=args.get("old_text"),
                new_text=args.get("new_text", ""),
            ),
            "create_directory": lambda: self.fs.create_directory(args.get("path", "")),
            "mkdir": lambda: self.fs.create_directory(args.get("path", "")),
            "search_files": lambda: self.fs.search_files(
                args.get("query", ""),
                path=args.get("path", "."),
            ),
            "run_tests": lambda: self.fs.run_tests(args.get("test_path")),
            "get_absolute_path": lambda: self.fs.get_absolute_path(args.get("path", ".")),
        }

        if action not in tool_map:
            raise ValueError(f"Unknown action: '{action}'. Available: {list(tool_map.keys())}")

        return tool_map[action]()

    # ======================================================
    # ACTION EXTRACTION
    # ======================================================

    @staticmethod
    def extract_actions_and_final(
        text: str,
    ) -> Tuple[List[Tuple[str, Dict[str, Any]]], Optional[str]]:
        """Extract structured ACTION calls and FINAL_ANSWER from model output."""
        final_ans = None
        if "FINAL_ANSWER:" in text:
            final_ans = text.split("FINAL_ANSWER:", 1)[1].strip()

        pattern = r"ACTION:\s*([a-zA-Z0-9_]+)(.*?)(?=(?:ACTION:|FINAL_ANSWER:|$))"
        matches = list(re.finditer(pattern, text, re.DOTALL | re.IGNORECASE))
        actions = []

        for m in matches:
            name = m.group(1).strip().lower()
            body = m.group(2).strip()
            args = {}
            arg_match = re.search(r"ARG(?:U)?MENTS:\s*(.*)", body, re.DOTALL | re.IGNORECASE)
            if arg_match:
                args_str = arg_match.group(1).strip()
                if "{" in args_str:
                    start = args_str.find("{")
                    brace_count = 0
                    end = -1
                    for i, c in enumerate(args_str[start:], start):
                        if c == "{":
                            brace_count += 1
                        elif c == "}":
                            brace_count -= 1
                            if brace_count == 0:
                                end = i + 1
                                break
                    if end != -1:
                        raw_json = args_str[start:end]
                        try:
                            args = json.loads(raw_json)
                        except Exception:
                            try:
                                args = json.loads(raw_json.replace("'", '"'))
                            except Exception:
                                pass
            actions.append((name, args))

        # If any action was actually final_answer, extract it as final_ans
        real_actions = []
        for name, args in actions:
            if name in ("final_answer", "finish", "complete"):
                if not final_ans:
                    if isinstance(args, dict) and args:
                        final_ans = (
                            args.get("message")
                            or args.get("answer")
                            or args.get("content")
                            or args.get("summary")
                            or json.dumps(args, ensure_ascii=False)
                        )
                    else:
                        final_ans = str(args or "")
            else:
                real_actions.append((name, args))

        return real_actions, final_ans

    @staticmethod
    def _summarize_tool_result(action: str, args: Dict[str, Any], result: Any) -> str:
        """Create a compact single-line summary of a tool execution for trajectory context."""
        path = args.get("path", "")
        if action == "list_files":
            count = len(result) if isinstance(result, list) else 0
            return f"list_files: found {count} items in '{path or '.'}'"
        elif action in ("write_file", "create_file"):
            bytes_w = (
                result.get("bytes_written", len(str(args.get("content", ""))))
                if isinstance(result, dict)
                else 0
            )
            return f"write_file: wrote '{path}' ({bytes_w} bytes)"
        elif action == "read_file":
            text = str(result)
            sample = text[:100] + ("..." if len(text) > 100 else "")
            return f'read_file: "{path}": {repr(sample)}'
        elif action in ("edit_file", "modify_file"):
            bytes_w = result.get("bytes", 0) if isinstance(result, dict) else 0
            return f"edit_file: modified '{path}' ({bytes_w} bytes)"
        elif action in ("create_directory", "mkdir"):
            return f"create_directory: created '{path}'"
        elif action == "get_absolute_path":
            return f"get_absolute_path: '{path}' -> {result}"
        elif action == "run_tests":
            succ = result.get("success", False) if isinstance(result, dict) else False
            return f"run_tests: {'passed' if succ else 'failed'}"
        else:
            return f"{action}: completed"

    @staticmethod
    def _format_compact_observation(action: str, result: Any) -> str:
        """Format compact observation text for the ReAct context."""
        if action == "list_files" and isinstance(result, list):
            sample = [f"{i.get('name')} ({i.get('type')})" for i in result[:8]]
            suffix = f" ... and {len(result) - 8} more" if len(result) > 8 else ""
            return f"Found {len(result)} items: {', '.join(sample)}{suffix}"
        elif action == "read_file":
            text = str(result)
            return text if len(text) <= 500 else text[:500] + "... [truncated]"
        elif isinstance(result, (dict, list)):
            return json.dumps(result, ensure_ascii=False)
        else:
            return str(result)[:500]

    # ======================================================
    # AUTONOMOUS STREAMING AGENT LOOP
    # ======================================================

    def stream_run(
        self,
        task: str,
        max_steps: int = 10,
    ) -> Generator[str, None, None]:
        """Execute a coding task through multi-step autonomous tool calls and stream updates."""
        task_str = str(task or "").strip()
        if not task_str:
            yield "Coding task is empty."
            return

        if hasattr(self.model, "is_available"):
            try:
                if not self.model.is_available():
                    yield (
                        f"Coding model '{getattr(self.model, 'model_name', 'default')}' is not available in Ollama."
                    )
                    return
            except Exception:
                pass

        history: List[Dict[str, str]] = []
        user_facing_history: List[str] = []

        for step in range(1, max_steps + 1):
            prompt_parts = [
                CODING_AGENT_SYSTEM_PROMPT.format(workspace=str(self.workspace)),
                f"\nUSER REQUEST:\n{task_str}\n",
            ]
            for item in history:
                if item["role"] == "assistant":
                    prompt_parts.append(f"Atlas:\n{item['content']}\n")
                elif item["role"] == "observation":
                    prompt_parts.append(f"OBSERVATION:\n{item['content']}\n")

            prompt_parts.append("Atlas:\n")
            prompt = "\n".join(prompt_parts)

            # Generate step with early break when complete action is formed
            tokens = []
            if hasattr(self.model, "stream_generate"):
                stream_iter = self.model.stream_generate(
                    prompt,
                    max_tokens=256,
                    stop=["\nOBSERVATION:", "OBSERVATION:"],
                )
            elif hasattr(self.model, "generate"):
                stream_iter = self.model.generate(prompt, stream=True)
            else:
                stream_iter = []

            for token in stream_iter:
                tokens.append(token)
                so_far = "".join(tokens)
                if "ACTION:" in so_far and ("ARGUMENTS:" in so_far or "ARGMENTS:" in so_far):
                    args_marker = "ARGUMENTS:" if "ARGUMENTS:" in so_far else "ARGMENTS:"
                    args_part = so_far[so_far.find(args_marker):].strip()
                    if "{" in args_part and "}" in args_part:
                        if "\n" in args_part[args_part.find("}"):]:
                            break

            raw_output = "".join(tokens).strip()
            if "OBSERVATION:" in raw_output:
                raw_output = raw_output[:raw_output.find("OBSERVATION:")].strip()

            actions, final_ans = self.extract_actions_and_final(raw_output)

            # If model produced a final answer and no more actions
            if not actions and final_ans is not None:
                yield final_ans
                return

            # If no structured action was detected
            if not actions:
                # If the raw output contains useful explanatory text or looks finished
                if raw_output and not raw_output.startswith("ACTION:"):
                    yield raw_output
                    return

                # Otherwise nudge with an observation
                history.append({"role": "assistant", "content": raw_output or "None"})
                history.append({
                    "role": "observation",
                    "content": "Error: No tool ACTION specified. Use ACTION: <tool_name> and ARGUMENTS: {...}.",
                })
                continue

            # Execute tool actions
            observations = []
            for action, raw_args in actions:
                args = self.normalize_args(action, raw_args)
                path_desc = args.get("path", "")
                progress_msg = f"• Executed `{action}`" + (f" on `{path_desc}`" if path_desc else "") + "\n"
                yield progress_msg
                user_facing_history.append(progress_msg)

                try:
                    tool_res = self.execute_tool(action, args)
                    compact_obs = self._format_compact_observation(action, tool_res)
                    observations.append(compact_obs)

                    if action == "read_file":
                        content_disp = f"  └─ Content: {repr(str(tool_res))}\n"
                        yield content_disp
                        user_facing_history.append(content_disp)
                    elif action == "get_absolute_path":
                        path_disp = f"  └─ Absolute path: {tool_res}\n"
                        yield path_disp
                        user_facing_history.append(path_disp)

                except Exception as exc:
                    err_msg = f"Error: {exc}"
                    observations.append(err_msg)
                    yield f"  └─ Error: {exc}\n"

            obs_text = "\n".join(observations)
            history.append({"role": "assistant", "content": raw_output})
            history.append({"role": "observation", "content": obs_text})

            # If final answer was also provided in the same turn
            if final_ans:
                yield f"\n{final_ans}\n"
                return

        # If max steps reached without explicit FINAL_ANSWER, synthesize result
        yield "\nTask completed. Operations performed:\n" + "".join(user_facing_history)
        if (self.workspace / "atlas_fs_test.txt").exists():
            abs_p = str((self.workspace / "atlas_fs_test.txt").resolve())
            yield f"\nFile absolute path: {abs_p}\n"

    def run(self, task: str) -> str:
        """Run the coding agent synchronously and return the full result string."""
        return "".join(self.stream_run(task)).strip()

    @staticmethod
    def _format_items(items):
        if not items:
            return "- None identified."
        return "\n".join(f"- {item}" for item in items)

    @staticmethod
    def _format_changes(change_set):
        if not change_set.changes:
            return "- No changes generated."
        results = []
        for change in change_set.changes:
            results.append(
                f"- FILE: {change.path}\n"
                f"  REASON: {change.reason}\n"
                f"  OLD_TEXT:\n{change.old_text}\n"
                f"  NEW_TEXT:\n{change.new_text}"
            )
        return "\n".join(results)
"""Safe workspace filesystem access and tool implementations for the Atlas Coding Agent."""

import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Union


class CodeFilesystem:
    """Safe, permission-enforced filesystem operations restricted to a canonical workspace."""

    def __init__(
        self,
        workspace: Optional[Union[str, Path]] = None,
        allow_write: bool = True,
        allow_tests: bool = True,
    ):
        self.workspace = Path(workspace or Path.cwd()).resolve()
        self.allow_write = bool(allow_write)
        self.allow_tests = bool(allow_tests)

    def _safe_path(self, path: Union[str, Path]) -> Path:
        """Resolve a path canonicalizing symlinks and ensuring it stays within workspace."""
        raw = str(path or "").strip()
        if not raw or raw == ".":
            return self.workspace

        target = (self.workspace / raw).resolve()

        if target != self.workspace and self.workspace not in target.parents:
            raise PermissionError(
                f"Path outside workspace: {path}"
            )

        return target

    def list_files(self, path: str = ".") -> List[Dict[str, Any]]:
        """List files and directories in the permitted workspace."""
        directory = self._safe_path(path)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")

        results = []
        ignored = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
        }

        for item in sorted(directory.iterdir()):
            if item.name in ignored:
                continue

            rel = item.relative_to(self.workspace)
            results.append(
                {
                    "name": item.name,
                    "path": str(rel),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                }
            )

        return results

    def read_file(self, path: str) -> str:
        """Read the contents of an existing permitted file."""
        target = self._safe_path(path)

        if not target.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not target.is_file():
            raise IsADirectoryError(f"Target is a directory: {path}")

        return target.read_text(
            encoding="utf-8",
            errors="replace",
        )

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Create a file or replace its contents."""
        if not self.allow_write:
            raise PermissionError("Write operations are disabled by permissions.")

        target = self._safe_path(path)

        if target.is_dir():
            raise IsADirectoryError(f"Cannot overwrite directory with file: {path}")

        target.parent.mkdir(parents=True, exist_ok=True)
        content_str = str(content if content is not None else "")
        target.write_text(content_str, encoding="utf-8")

        return {
            "success": True,
            "path": str(target.relative_to(self.workspace)),
            "absolute_path": str(target),
            "bytes_written": len(content_str.encode("utf-8")),
        }

    def edit_file(
        self,
        path: str,
        old_text: Optional[str] = None,
        new_text: str = "",
    ) -> Dict[str, Any]:
        """Make a validated change to an existing file."""
        if not self.allow_write:
            raise PermissionError("Write operations are disabled by permissions.")

        target = self._safe_path(path)

        if not target.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not target.is_file():
            raise IsADirectoryError(f"Target is a directory: {path}")

        current_content = target.read_text(encoding="utf-8", errors="replace")
        new_text_str = str(new_text if new_text is not None else "")

        if old_text is None or old_text == "":
            updated = new_text_str
        elif old_text in current_content:
            count = current_content.count(old_text)
            if count > 1:
                raise ValueError(
                    f"Ambiguous replacement: target text appears {count} times in '{path}'."
                )
            updated = current_content.replace(old_text, new_text_str, 1)
        else:
            stripped_old = old_text.strip()
            if stripped_old and stripped_old in current_content:
                count = current_content.count(stripped_old)
                if count == 1:
                    updated = current_content.replace(stripped_old, new_text_str, 1)
                else:
                    raise ValueError(
                        f"Ambiguous replacement: stripped target text appears {count} times in '{path}'."
                    )
            else:
                raise ValueError(
                    f"Target text to replace was not found in '{path}'."
                )

        target.write_text(updated, encoding="utf-8")

        return {
            "success": True,
            "path": str(target.relative_to(self.workspace)),
            "absolute_path": str(target),
            "bytes": len(updated.encode("utf-8")),
        }

    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory within the workspace."""
        if not self.allow_write:
            raise PermissionError("Write operations are disabled by permissions.")

        target = self._safe_path(path)
        target.mkdir(parents=True, exist_ok=True)

        return {
            "success": True,
            "path": str(target.relative_to(self.workspace)),
            "absolute_path": str(target),
        }

    def search_files(self, query: str, path: str = ".") -> str:
        """Search relevant workspace files for a string."""
        search_dir = self._safe_path(path)
        if not search_dir.is_dir():
            raise NotADirectoryError(str(search_dir))

        query_str = str(query or "").strip()
        if not query_str:
            return ""

        rg_path = shutil.which("rg")
        if rg_path:
            try:
                res = subprocess.run(
                    [
                        rg_path,
                        "--line-number",
                        "--max-count",
                        "30",
                        "--glob",
                        "!.git/**",
                        "--glob",
                        "!.venv/**",
                        "--glob",
                        "!venv/**",
                        "--glob",
                        "!__pycache__/**",
                        "--glob",
                        "!*.pyc",
                        "--",
                        query_str,
                        str(search_dir),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if res.stdout:
                    return res.stdout[:10000]
            except Exception:
                pass

        # Fallback pure Python search
        matches = []
        ignored = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules"}
        for p in search_dir.rglob("*"):
            if any(part in ignored for part in p.parts):
                continue
            if p.is_file():
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    for i, line in enumerate(text.splitlines(), start=1):
                        if query_str.lower() in line.lower():
                            rel = p.relative_to(self.workspace)
                            matches.append(f"{rel}:{i}: {line.strip()}")
                            if len(matches) >= 30:
                                break
                except Exception:
                    continue
            if len(matches) >= 30:
                break

        return "\n".join(matches)

    def run_tests(self, test_path: Optional[str] = None) -> Dict[str, Any]:
        """Run project tests through a controlled execution mechanism."""
        if not self.allow_tests:
            raise PermissionError("Running tests is disabled by permissions.")

        pytest_bin = (
            self.workspace / ".venv" / "bin" / "pytest"
            if (self.workspace / ".venv" / "bin" / "pytest").exists()
            else shutil.which("pytest") or "pytest"
        )

        cmd = [str(pytest_bin), "-v"]
        if test_path:
            safe_t = self._safe_path(test_path)
            cmd.append(str(safe_t))

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=45,
            )
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout[-5000:],
                "stderr": result.stderr[-2000:],
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "Test execution timed out after 45 seconds.",
                "success": False,
            }
        except Exception as exc:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(exc),
                "success": False,
            }

    def get_absolute_path(self, path: str) -> str:
        """Return the canonical absolute path of a permitted file/directory."""
        return str(self._safe_path(path))

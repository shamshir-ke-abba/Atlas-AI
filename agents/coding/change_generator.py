"""
Generate structured, controlled code changes for Atlas Coding Agent.

The generator proposes changes but does not modify files.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class CodeChange:
    path: str
    old_text: str
    new_text: str
    reason: str = ""


@dataclass
class ChangeSet:
    changes: List[CodeChange] = field(
        default_factory=list
    )


class CodingChangeGenerator:
    """Generate exact text replacements from a coding task."""

    def __init__(self, model=None):
        self.model = model

    def generate(
        self,
        task: str,
        plan,
        repository_context: str,
    ) -> ChangeSet:
        task = str(task or "").strip()
        repository_context = str(
            repository_context or ""
        ).strip()

        if not task:
            return ChangeSet()

        if self.model is None:
            return ChangeSet()

        prompt = f"""
You are the change-generation component of Atlas Coding Agent.

USER TASK:
{task}

PLAN:
OBJECTIVE:
{plan.objective}

FILES TO INSPECT:
{self._format_items(plan.files_to_inspect)}

CHANGES:
{self._format_items(plan.changes)}

TESTS:
{self._format_items(plan.tests)}

RISKS:
{self._format_items(plan.risks)}

REPOSITORY CONTEXT:
{repository_context}

Generate the smallest safe code changes required.

Rules:
- Only modify files visible in the repository context.
- Do not invent files.
- Do not rewrite an entire file unless absolutely necessary.
- Use exact existing text for OLD_TEXT.
- OLD_TEXT must occur exactly once in the target file.
- NEW_TEXT must contain the complete replacement.
- Do not execute commands.
- Do not claim that changes were applied.

Return exactly this format:

CHANGE:
PATH:
<repository-relative path>
OLD_TEXT:
<exact existing text>
NEW_TEXT:
<replacement text>
REASON:
<short reason>

Repeat CHANGE sections for additional changes.
""".strip()

        response = self.model.generate(prompt)

        return self._parse_response(
            response
        )

    @staticmethod
    def _parse_response(response):
        changes = []

        current = None
        section = None

        for raw_line in str(response or "").splitlines():
            line = raw_line.rstrip()

            if line.strip().upper() == "CHANGE:":
                if current is not None:
                    parsed = CodingChangeGenerator._build_change(
                        current
                    )

                    if parsed is not None:
                        changes.append(parsed)

                current = {}
                section = None
                continue

            if current is None:
                continue

            stripped = line.strip()

            for name in (
                "PATH:",
                "OLD_TEXT:",
                "NEW_TEXT:",
                "REASON:",
            ):
                if stripped.upper() == name:
                    section = name[:-1]
                    current.setdefault(
                        section,
                        [],
                    )
                    break
            else:
                if section is not None:
                    current[section].append(
                        line
                    )

        if current is not None:
            parsed = CodingChangeGenerator._build_change(
                current
            )

            if parsed is not None:
                changes.append(parsed)

        return ChangeSet(
            changes=changes
        )

    @staticmethod
    def _build_change(data):
        path = "\n".join(
            data.get("PATH", [])
        ).strip()

        old_text = "\n".join(
            data.get("OLD_TEXT", [])
        )

        new_text = "\n".join(
            data.get("NEW_TEXT", [])
        )

        reason = "\n".join(
            data.get("REASON", [])
        ).strip()

        if not path or not old_text:
            return None

        return CodeChange(
            path=path,
            old_text=old_text,
            new_text=new_text,
            reason=reason,
        )

    @staticmethod
    def _format_items(items):
        if not items:
            return "- None identified."

        return "\n".join(
            f"- {item}"
            for item in items
        )
"""
Planning layer for the Atlas Coding Agent.

The planner does not modify files or execute commands.
It converts a coding task and repository context into
a structured plan for the execution layer.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class CodingPlan:
    objective: str
    files_to_inspect: List[str] = field(
        default_factory=list
    )
    changes: List[str] = field(
        default_factory=list
    )
    tests: List[str] = field(
        default_factory=list
    )
    risks: List[str] = field(
        default_factory=list
    )


class CodingPlanner:
    """Create structured plans for coding tasks."""

    def __init__(self, model=None):
        self.model = model

    def create_plan(
        self,
        task: str,
        repository_context: str,
    ) -> CodingPlan:
        task = str(task or "").strip()
        repository_context = str(
            repository_context or ""
        ).strip()

        if not task:
            return CodingPlan(
                objective="No coding task provided."
            )

        if self.model is None:
            return self._fallback_plan(task)

        prompt = f"""
You are the planning component of Atlas Coding Agent.

USER TASK:
{task}

REPOSITORY CONTEXT:
{repository_context}

Create a precise coding plan.

Rules:
- Do not modify files.
- Do not claim anything was changed.
- Only reference files visible in the repository context.
- Prefer the smallest correct change.
- Preserve existing architecture.
- Include tests that should be run.
- Mention important risks.

Return the plan using exactly these sections:

OBJECTIVE:
FILES_TO_INSPECT:
CHANGES:
TESTS:
RISKS:
""".strip()

        response = self.model.generate(prompt)

        return self._parse_plan(
            task,
            response,
        )

    @staticmethod
    def _fallback_plan(task: str) -> CodingPlan:
        return CodingPlan(
            objective=task,
            changes=[
                "Inspect the relevant implementation.",
                "Make the smallest correct change.",
                "Preserve existing architecture.",
            ],
            tests=[
                "Run the relevant pytest tests.",
                "Run the full test suite.",
            ],
            risks=[
                "The change may affect existing behavior.",
            ],
        )

    @staticmethod
    def _parse_plan(
        task: str,
        response: str,
    ) -> CodingPlan:
        sections = {
            "OBJECTIVE": [],
            "FILES_TO_INSPECT": [],
            "CHANGES": [],
            "TESTS": [],
            "RISKS": [],
        }

        current = None

        for raw_line in str(response or "").splitlines():
            line = raw_line.strip()

            if not line:
                continue

            normalized = line.rstrip(":").upper()

            if normalized in sections:
                current = normalized
                continue

            if current is not None:
                cleaned = line.lstrip(
                    "-*0123456789. "
                ).strip()

                if cleaned:
                    sections[current].append(
                        cleaned
                    )

        objective = (
            sections["OBJECTIVE"][0]
            if sections["OBJECTIVE"]
            else task
        )

        return CodingPlan(
            objective=objective,
            files_to_inspect=sections[
                "FILES_TO_INSPECT"
            ],
            changes=sections["CHANGES"],
            tests=sections["TESTS"],
            risks=sections["RISKS"],
        )
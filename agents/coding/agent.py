from pathlib import Path

from agents.coding.model import CodingModel
from agents.coding.prompts import CODING_SYSTEM_PROMPT
from agents.coding.tools.filesystem import CodeFilesystem
from agents.coding.tools.search import CodeSearch


class CodingAgent:

    def __init__(self, workspace=None, model=None):
        self.workspace = Path(
            workspace or Path.cwd()
        ).resolve()

        self.model = model or CodingModel()

        self.filesystem = CodeFilesystem(
            self.workspace
        )

        self.searcher = CodeSearch(
            self.workspace
        )

    def inspect(self, task):
        """Give the model real repository information."""

        files = self.filesystem.list_files(".")

        file_list = "\n".join(
            f"- {item['name']} ({item['type']})"
            for item in files
        )

        search_results = self.searcher.search(task)

        return f"""
PROJECT FILES:
{file_list}

SEARCH RESULTS:
{search_results or "No direct matches found."}
""".strip()

    def build_prompt(self, task):
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

    def run(self, task):
        task = str(task or "").strip()

        if not task:
            return "Coding task is empty."

        if not self.model.is_available():
            return (
                f"Coding model '{self.model.model_name}' "
                "is not available in Ollama."
            )

        prompt = self.build_prompt(task)

        return self.model.generate(prompt)

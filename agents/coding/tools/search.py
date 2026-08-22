import subprocess


class CodeSearch:
    """Search source code using ripgrep."""

    def __init__(self, workspace):
        self.workspace = str(workspace)

    def search(self, query):
        result = subprocess.run(
            [
                "rg",
                "--line-number",
                "--hidden",
                "--glob", "!.git/**",
                "--glob", "!.venv/**",
                "--glob", "!venv/**",
                "--glob", "!__pycache__/**",
                "--glob", "!*.pyc",
                query,
                self.workspace,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )

        return result.stdout[:20000]

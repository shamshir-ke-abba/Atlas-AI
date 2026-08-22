"""
Atlas Coding Agent Model

Dedicated local model interface for coding tasks.
"""

import json
import logging
import requests


logger = logging.getLogger(__name__)


class CodingModel:
    """
    Local Ollama model dedicated to coding.

    This is intentionally separate from AtlasModel so the normal
    Atlas assistant and coding agent can use different models.
    """

    def __init__(
        self,
        model_name: str = "qwen2.5:1.5b",
        host: str = "http://localhost:11434",
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ):
        self.model_name = model_name
        self.host = host
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, prompt: str) -> str:
        """Generate one complete coding-agent response."""

        url = f"{self.host}/api/generate"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "num_predict": self.max_tokens,
            },
        }

        response = requests.post(
            url,
            json=payload,
            timeout=(10, 600),
        )

        response.raise_for_status()

        data = response.json()

        return str(
            data.get("response", "")
        ).strip()

    def is_available(self) -> bool:
        """Check whether Ollama and the coding model are available."""

        try:
            response = requests.get(
                f"{self.host}/api/tags",
                timeout=5,
            )

            if response.status_code != 200:
                return False

            data = response.json()

            models = data.get("models", [])

            for model in models:
                name = str(
                    model.get("name", "")
                )

                if name == self.model_name:
                    return True

            return False

        except Exception:
            return False

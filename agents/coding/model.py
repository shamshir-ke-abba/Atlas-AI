"""Atlas Coding Agent Model

Dedicated local model interface for coding tasks.
"""

import json
import logging
import requests
from typing import Generator, List, Optional

from config import MODEL_NAME, OLLAMA_HOST

logger = logging.getLogger(__name__)


class CodingModel:
    """Local Ollama model dedicated to coding tasks."""

    def __init__(
        self,
        model_name: str = MODEL_NAME,
        host: str = OLLAMA_HOST,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ):
        self.model_name = model_name
        self.host = host
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, prompt: str) -> str:
        """Generate one complete coding-agent response."""
        chunks = list(self.stream_generate(prompt))
        return "".join(chunks).strip()

    def stream_generate(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """Stream tokens from Ollama with optional stop patterns."""
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": True,
            "keep_alive": "10m",
            "options": {
                "num_predict": max_tokens or self.max_tokens,
            },
        }

        try:
            response = requests.post(
                url,
                json=payload,
                stream=True,
                timeout=(10, 300),
            )
            response.raise_for_status()

            accumulated = []
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                token = data.get("response", "")
                if token:
                    accumulated.append(token)
                    yield token

                    # Check stop condition if provided
                    if stop:
                        text_so_far = "".join(accumulated)
                        if any(s in text_so_far for s in stop):
                            break

                if data.get("done", False):
                    break

        except Exception as exc:
            logger.error("CodingModel stream_generate error: %s", exc)
            yield f"\n[Model Error: {exc}]\n"

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
            target = self.model_name.split(":")[0]

            for model in models:
                name = str(model.get("name", ""))
                if name == self.model_name or name.startswith(f"{target}:"):
                    return True

            return False
        except Exception:
            return False

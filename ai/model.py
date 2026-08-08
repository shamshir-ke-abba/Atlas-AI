"""
Atlas V3 Model

Handles communication with the local Ollama model.
"""

import ollama

from ai.prompts import SYSTEM_PROMPT
from config import (
    MODEL_NAME,
    OLLAMA_HOST,
    TEMPERATURE,
)


class AtlasModel:

    def __init__(self):
        self.model = MODEL_NAME

        self.client = ollama.Client(
            host=OLLAMA_HOST
        )

    def generate(self, prompt):

        stream = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            options={
                "temperature": TEMPERATURE,
            },
            stream=True,
        )

        for chunk in stream:

            content = (
                chunk
                .get("message", {})
                .get("content", "")
            )

            if content:
                yield content

    def clear_history(self):
        """
        Kept for compatibility.

        Conversation history is managed by
        ConversationManager rather than the model.
        """
        pass
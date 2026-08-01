"""
Atlas Model

Handles communication with the local LLM.
"""

import ollama


class AtlasModel:

    def __init__(self):

        self.model = "qwen2.5:1.5b"

    def generate(
        self,
        prompt,
    ):

        stream = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            stream=True,
        )

        for chunk in stream:

            content = chunk["message"]["content"]

            if content:

                yield content
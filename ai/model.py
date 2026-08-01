"""
Atlas Model

Handles communication with the local LLM.
"""

import ollama


class AtlasModel:

    def __init__(self):

        self.model = "qwen2.5:1.5b"

        self.history = []

    def generate(
        self,
        prompt,
    ):

        self.history.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        stream = ollama.chat(
            model=self.model,
            messages=self.history,
            stream=True,
        )

        assistant_reply = ""

        for chunk in stream:

            content = chunk["message"]["content"]

            if content:

                assistant_reply += content

                yield content

        self.history.append(
            {
                "role": "assistant",
                "content": assistant_reply,
            }
        )

    def clear_history(self):

        self.history.clear()
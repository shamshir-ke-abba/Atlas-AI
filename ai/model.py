"""
Atlas Model

Handles communication with the local LLM.
"""

import ollama
from ai.prompts import SYSTEM_PROMPT


class AtlasModel:

    def __init__(self):

        self.model = "qwen2.5:1.5b"

        self.history = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

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

        print("\n========== HISTORY ==========")

        for i, msg in enumerate(self.history):

            print(
                f"{i}: {msg['role']} -> {msg['content']}"
            )

        print("=============================\n")

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

        self.history = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]
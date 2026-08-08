"""
Atlas V3 Context Builder
"""

from core.memory import MemoryManager


class ContextBuilder:

    def __init__(self):
        self.memory = MemoryManager()

    def build(
        self,
        history,
        message,
        is_hinglish=False,
    ):
        parts = []

        # --------------------------------------------------
        # Hinglish Context
        # --------------------------------------------------

        if is_hinglish:
            parts.append(
                "NOTE: User may be speaking in Hinglish/Hindi. "
                "Respond clearly and helpfully."
            )

        # --------------------------------------------------
        # System Context
        # --------------------------------------------------

        memory = self.memory.all()

        if memory:

            parts.append(
                "=== USER MEMORY ==="
            )

            for category, values in memory.items():

                parts.append(
                    f"[{category}]"
                )

                if isinstance(values, dict):

                    for key, value in values.items():

                        parts.append(
                            f"{key}: {value}"
                        )

                else:

                    parts.append(
                        str(values)
                    )

        # --------------------------------------------------
        # Conversation
        # --------------------------------------------------

        if history:

            parts.append(
                "\n=== RECENT CHAT ==="
            )

            for item in history:

                role = item["role"].capitalize()

                parts.append(
                    f"{role}: {item['content']}"
                )

        # --------------------------------------------------
        # Current Message
        # --------------------------------------------------

        parts.append(
            "\n=== CURRENT USER MESSAGE ==="
        )

        parts.append(message)

        return "\n".join(parts)
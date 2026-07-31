"""
Atlas AI Model Interface

Handles communication with
the language model backend.
"""


class AtlasModel:

    def __init__(self):

        self.name = "Atlas Local Model"


    # =====================================================
    # Generation
    # =====================================================

    def generate(
        self,
        prompt
    ):

        """
        Generate a response.

        Temporary placeholder until
        the real LLM backend is connected.
        """

        return (
            "I am currently connected "
            "to the Atlas model interface."
        )
"""
Atlas Brain

Coordinates reasoning before talking
to the model.
"""

from ai.model import AtlasModel


class AtlasBrain:

    def __init__(self):

        self.model = AtlasModel()

    def process(
        self,
        message,
    ):

        yield from self.model.generate(
            message
        )
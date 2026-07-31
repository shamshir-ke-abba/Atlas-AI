"""
Atlas AI Brain

Coordinates prompts,
memory and model responses.
"""

from ai.model import AtlasModel
from ai.prompts import ATLAS_SYSTEM_PROMPT


class AtlasBrain:

    def __init__(self):

        self.model = AtlasModel()

        self.system_prompt = ATLAS_SYSTEM_PROMPT


    # =====================================================
    # Processing
    # =====================================================

    def process(
        self,
        message
    ):

        prompt = f"""
{self.system_prompt}

User:
{message}
"""


        response = self.model.generate(
            prompt
        )

        return response
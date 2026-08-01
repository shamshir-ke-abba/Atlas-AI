"""
Atlas Brain
"""

import time


class AtlasBrain:

    def process(
        self,
        message,
    ):

        response = (
            "Hello! I'm Atlas. "
            "Streaming is now working."
        )

        words = response.split()

        current = ""

        for word in words:

            current += word + " "

            

            yield current
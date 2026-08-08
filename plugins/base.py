"""
Atlas Plugin Base
"""


class AtlasPlugin:

    name = ""

    description = ""

    triggers = []

    capabilities = []

    priority = 100

    enabled = True

    version = "1.0"

    author = "Atlas"

    def can_handle(
        self,
        message,
    ):
        """
        Determines whether this plugin should handle
        the given message.

        Plugins can override this for more specific
        intent detection.
        """

        return False

    def run(
        self,
        **kwargs,
    ):

        raise NotImplementedError
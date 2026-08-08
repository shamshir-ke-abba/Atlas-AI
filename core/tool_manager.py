"""
Atlas Tool Manager

Wrapper around the Plugin Manager.
"""

from core.plugin_manager import PluginManager


class ToolManager:

    def __init__(self):

        self.plugins = PluginManager()

    def execute(
        self,
        name,
        **kwargs,
    ):

        return self.plugins.execute(
            name,
            **kwargs,
        )

    def available(self):

        return self.plugins.available()
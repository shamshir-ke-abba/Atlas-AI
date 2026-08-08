"""
Atlas V3 Plugin Manager
"""

import importlib
import inspect
import pkgutil

from plugins.base import AtlasPlugin


class PluginManager:

    def __init__(self):

        self.plugins = {}

        self.load_plugins()

    # ==================================================
    # Loading
    # ==================================================

    def load_plugins(self):

        import plugins.system

        for _, module_name, _ in pkgutil.iter_modules(
            plugins.system.__path__
        ):

            module = importlib.import_module(
                f"plugins.system.{module_name}"
            )

            for _, obj in inspect.getmembers(
                module,
                inspect.isclass,
            ):

                if not issubclass(
                    obj,
                    AtlasPlugin,
                ):
                    continue

                if obj is AtlasPlugin:
                    continue

                plugin = obj()

                if not plugin.enabled:
                    continue

                if not plugin.name:
                    continue

                self.plugins[
                    plugin.name
                ] = plugin

    # ==================================================
    # Execution
    # ==================================================

    def execute(
        self,
        name,
        **kwargs,
    ):

        plugin = self.plugins.get(name)

        if plugin is None:
            raise ValueError(
                f"Unknown plugin: {name}"
            )

        return plugin.run(
            **kwargs
        )

    # ==================================================
    # Information
    # ==================================================

    def available(self):

        return list(
            self.plugins.keys()
        )
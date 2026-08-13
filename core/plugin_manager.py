"""
Atlas Plugin Manager

Discovers and manages Atlas plugins.
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
    # Load Plugins
    # ==================================================

    def load_plugins(self):
        """
        Load all Atlas plugins from supported packages.
        """

        # System plugins
        self._load_package(
            "plugins.system"
        )

        # Math engine plugins
        self._load_package(
            "plugins.math_engine"
        )

    # ==================================================
    # Load Package
    # ==================================================

    def _load_package(
        self,
        package_name,
    ):
        """
        Discover Python modules inside a package.
        """

        try:
            package = importlib.import_module(
                package_name
            )
        except Exception as exc:
            print(
                f"Failed to load package "
                f"{package_name}: {exc}"
            )
            return

        for _, module_name, is_package in pkgutil.iter_modules(
            package.__path__
        ):

            # ------------------------------------------
            # Skip sub-packages
            # ------------------------------------------

            if is_package:
                continue

            full_module_name = (
                f"{package_name}.{module_name}"
            )

            try:
                module = importlib.import_module(
                    full_module_name
                )

            except Exception as exc:
                print(
                    f"Failed to load module "
                    f"{full_module_name}: {exc}"
                )
                continue

            self._load_module(
                module
            )

    # ==================================================
    # Load Module
    # ==================================================

    def _load_module(
        self,
        module,
    ):
        """
        Find and register AtlasPlugin classes
        defined inside a module.
        """

        for _, obj in inspect.getmembers(
            module,
            inspect.isclass,
        ):

            # ------------------------------------------
            # Must be an Atlas plugin
            # ------------------------------------------

            try:
                is_plugin = issubclass(
                    obj,
                    AtlasPlugin,
                )
            except TypeError:
                continue

            if not is_plugin:
                continue

            # ------------------------------------------
            # Don't register base class
            # ------------------------------------------

            if obj is AtlasPlugin:
                continue

            # ------------------------------------------
            # Only register classes defined in module
            # ------------------------------------------

            if obj.__module__ != module.__name__:
                continue

            # ------------------------------------------
            # Instantiate
            # ------------------------------------------

            try:

                plugin = obj()

            except Exception as exc:

                print(
                    f"Failed to load plugin "
                    f"{obj.__name__}: {exc}"
                )

                continue

            # ------------------------------------------
            # Validate name
            # ------------------------------------------

            name = getattr(
                plugin,
                "name",
                None,
            )

            if not name:

                print(
                    f"Skipping plugin "
                    f"{obj.__name__}: "
                    f"missing name"
                )

                continue

            # ------------------------------------------
            # Prevent duplicate names
            # ------------------------------------------

            if name in self.plugins:

                print(
                    f"Skipping duplicate plugin: "
                    f"{name}"
                )

                continue

            # ------------------------------------------
            # Register
            # ------------------------------------------

            self.plugins[
                name
            ] = plugin

            print(
                f"Loaded plugin: {name}"
            )

    # ==================================================
    # Execute
    # ==================================================

    def execute(
        self,
        name,
        **kwargs,
    ):
        """
        Execute a registered plugin.
        """

        if name not in self.plugins:

            raise ValueError(
                f"Unknown tool: {name}"
            )

        plugin = self.plugins[
            name
        ]

        return plugin.run(
            **kwargs
        )

    # ==================================================
    # Get Plugin
    # ==================================================

    def get(
        self,
        name,
    ):
        """
        Return a plugin instance by name.
        """

        return self.plugins.get(
            name
        )

    # ==================================================
    # Available
    # ==================================================

    def available(self):
        """
        Return all registered plugin names.
        """

        return list(
            self.plugins.keys()
        )
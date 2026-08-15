"""
Atlas V3 Plugin Manager

Discovers, loads and manages Atlas plugins.

The plugin manager is deliberately independent from
AtlasBrain and ToolManager.
"""

import importlib
import inspect
import logging
import pkgutil

from plugins.base import AtlasPlugin


logger = logging.getLogger("atlas")


class PluginManager:
    """Central plugin discovery and registry."""

    PACKAGES = (
        "plugins.system",
        "plugins.math_engine",
    )

    def __init__(self):
        self.plugins = {}
        self.load_plugins()

    # =========================================================
    # LOAD
    # =========================================================

    def load_plugins(self):
        """Load every plugin from configured plugin packages."""

        self.plugins.clear()

        for package_name in self.PACKAGES:
            self._load_package(package_name)

        logger.info(
            "Plugin system loaded: %s",
            self.available(),
        )

    # =========================================================
    # PACKAGE DISCOVERY
    # =========================================================

    def _load_package(self, package_name):
        try:
            package = importlib.import_module(package_name)

        except Exception as exc:
            logger.exception(
                "Failed to import plugin package '%s': %s",
                package_name,
                exc,
            )
            return

        package_path = getattr(
            package,
            "__path__",
            None,
        )

        if package_path is None:
            return

        for _, module_name, is_package in pkgutil.iter_modules(
            package_path
        ):

            if is_package:
                continue

            module_name = str(module_name)

            # Never load Python cache/helper modules.
            if module_name.startswith("_"):
                continue

            full_name = (
                f"{package_name}.{module_name}"
            )

            try:
                module = importlib.import_module(
                    full_name
                )

            except Exception as exc:
                # One broken plugin must not prevent every
                # other plugin from loading.
                logger.exception(
                    "Failed to load plugin module '%s': %s",
                    full_name,
                    exc,
                )
                continue

            self._load_module(module)

    # =========================================================
    # MODULE
    # =========================================================

    def _load_module(self, module):
        """Find AtlasPlugin subclasses defined in a module."""

        for _, obj in inspect.getmembers(
            module,
            inspect.isclass,
        ):

            try:
                is_plugin = issubclass(
                    obj,
                    AtlasPlugin,
                )

            except TypeError:
                continue

            if not is_plugin:
                continue

            if obj is AtlasPlugin:
                continue

            # Only classes actually defined inside this module.
            if obj.__module__ != module.__name__:
                continue

            try:
                plugin = obj()

            except Exception as exc:
                logger.exception(
                    "Failed to instantiate plugin '%s': %s",
                    obj.__name__,
                    exc,
                )
                continue

            name = getattr(
                plugin,
                "name",
                None,
            )

            if not name:
                logger.warning(
                    "Skipping plugin '%s': missing name",
                    obj.__name__,
                )
                continue

            # Canonical plugin IDs are lowercase.
            name = str(name).strip().lower()

            if not name:
                continue

            # Keep plugin object's name canonical too.
            try:
                plugin.name = name
            except Exception:
                pass

            if name in self.plugins:
                logger.warning(
                    "Skipping duplicate plugin '%s' from %s",
                    name,
                    module.__name__,
                )
                continue

            self.plugins[name] = plugin

            logger.info(
                "Loaded plugin: %s",
                name,
            )

    # =========================================================
    # EXECUTION
    # =========================================================

    def execute(self, name, **kwargs):
        name = str(name).strip().lower()

        plugin = self.get(name)

        if plugin is None:
            raise ValueError(
                f"Unknown tool: {name}"
            )

        if not getattr(
            plugin,
            "enabled",
            True,
        ):
            raise RuntimeError(
                f"Tool is disabled: {name}"
            )

        return plugin.run(
            **kwargs
        )

    # =========================================================
    # GET
    # =========================================================

    def get(self, name):
        if not name:
            return None

        return self.plugins.get(
            str(name).strip().lower()
        )

    # =========================================================
    # AVAILABLE
    # =========================================================

    def available(self):
        return list(
            self.plugins.keys()
        )

    # =========================================================
    # METADATA
    # =========================================================

    def metadata(self):
        return [
            plugin.info()
            for plugin in self.plugins.values()
        ]

    # =========================================================
    # STATUS
    # =========================================================

    def status(self):
        enabled = 0
        disabled = 0

        for plugin in self.plugins.values():

            if getattr(
                plugin,
                "enabled",
                True,
            ):
                enabled += 1
            else:
                disabled += 1

        return {
            "total": len(self.plugins),
            "enabled": enabled,
            "disabled": disabled,
            "tools": self.available(),
        }
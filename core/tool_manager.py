"""
Atlas V3 Tool Manager

Central interface for Atlas tools/plugins.

Responsibilities:
- Load and expose plugins
- Find the best tool for a message
- Execute tools safely
- Normalize tool execution
- Provide tool metadata
- Keep routing logic out of AtlasBrain
"""

from typing import Any, Optional

from core.plugin_manager import PluginManager
from core.logger import logger


class ToolManager:
    """Central manager for Atlas tools."""

    def __init__(self):
        self.plugins = PluginManager()

        logger.info(
            "Available Atlas tools: %s",
            self.available(),
        )

    # ==================================================
    # EXECUTION
    # ==================================================

    def execute(
        self,
        name: str,
        message: str = "",
        **kwargs,
    ) -> Any:
        """
        Execute a registered tool by name.

        The message is passed through to PluginManager,
        which remains responsible for the actual plugin
        execution contract.
        """

        if not name:
            raise ValueError(
                "Tool name is required."
            )

        logger.info(
            "Executing tool: %s",
            name,
        )

        plugin = self.get(name)

        if plugin is None:
            raise ValueError(
                f"Tool not found: {name}"
            )

        return self.execute_plugin(
            plugin,
            message=message,
            **kwargs,
        )

    # --------------------------------------------------

    def execute_plugin(
        self,
        plugin,
        message: str = "",
        **kwargs,
    ) -> Any:
        """
        Execute a plugin while adapting to common
        Atlas plugin APIs.

        Supported forms:

            plugin.run(message)
            plugin.run(message=message)
            plugin.run(query=message)
            plugin.run(expression=...)
            plugin.run(**kwargs)

        Plugin-specific kwargs take priority.
        """

        if plugin is None:
            raise ValueError(
                "Plugin is required."
            )

        if not hasattr(plugin, "run"):
            raise TypeError(
                "Invalid plugin: missing run() method."
            )

        # --------------------------------------------------
        # Explicit kwargs
        # --------------------------------------------------

        if kwargs:

            try:
                return plugin.run(
                    **kwargs
                )

            except TypeError:
                pass

        # --------------------------------------------------
        # Standard message API
        # --------------------------------------------------

        try:
            return plugin.run(
                message
            )

        except TypeError:
            pass

        # --------------------------------------------------
        # Keyword message API
        # --------------------------------------------------

        try:
            return plugin.run(
                message=message
            )

        except TypeError:
            pass

        # --------------------------------------------------
        # Query API
        # --------------------------------------------------

        try:
            return plugin.run(
                query=message
            )

        except TypeError:
            pass

        # --------------------------------------------------
        # Let the original error surface if the plugin
        # does not support any known execution contract.
        # --------------------------------------------------

        return plugin.run(
            message
        )

    # ==================================================
    # GET
    # ==================================================

    def get(
        self,
        name: str,
    ):
        """
        Return a plugin instance by name.
        """

        if not name:
            return None

        return self.plugins.get(
            name
        )

    # ==================================================
    # AVAILABLE
    # ==================================================

    def available(self):
        """
        Return all registered tool names.
        """

        return self.plugins.available()

    # ==================================================
    # MATCH
    # ==================================================

    def match(
        self,
        message: str,
    ) -> Optional[Any]:
        """
        Find the best tool capable of handling a message.

        Uses each plugin's own can_handle() method.

        Lower priority number = higher priority.
        """

        if not message:
            return None

        message = str(
            message
        ).strip()

        if not message:
            return None

        candidates = []

        for name in self.available():

            plugin = self.get(
                name
            )

            if plugin is None:
                continue

            # ------------------------------------------
            # Disabled plugin
            # ------------------------------------------

            if not getattr(
                plugin,
                "enabled",
                True,
            ):
                continue

            # ------------------------------------------
            # Ask plugin whether it can handle message
            # ------------------------------------------

            if not hasattr(
                plugin,
                "can_handle",
            ):
                continue

            try:

                can_handle = plugin.can_handle(
                    message
                )

            except Exception as exc:

                logger.warning(
                    "Tool '%s' can_handle() failed: %s",
                    name,
                    exc,
                )

                continue

            if not can_handle:
                continue

            # ------------------------------------------
            # Priority
            # ------------------------------------------

            priority = getattr(
                plugin,
                "priority",
                100,
            )

            try:
                priority = int(
                    priority
                )
            except (
                TypeError,
                ValueError,
            ):
                priority = 100

            candidates.append(
                (
                    priority,
                    name,
                    plugin,
                )
            )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: (
                item[0],
                item[1].lower(),
            )
        )

        selected = candidates[0]

        logger.info(
            "Tool match: %s",
            selected[1],
        )

        return selected[2]

    # ==================================================
    # MATCH NAME
    # ==================================================

    def match_name(
        self,
        message: str,
    ) -> Optional[str]:
        """
        Return the name of the best matching tool.
        """

        plugin = self.match(
            message
        )

        if plugin is None:
            return None

        return getattr(
            plugin,
            "name",
            None,
        )

    # ==================================================
    # TOOL INFO
    # ==================================================

    def metadata(self):
        """
        Return metadata for all loaded tools.
        """

        result = []

        for plugin in self.plugins.plugins.values():

            result.append(
                {
                    "name": getattr(
                        plugin,
                        "name",
                        "",
                    ),

                    "display_name": getattr(
                        plugin,
                        "display_name",
                        getattr(
                            plugin,
                            "name",
                            "",
                        ),
                    ),

                    "description": getattr(
                        plugin,
                        "description",
                        "",
                    ),

                    "icon": getattr(
                        plugin,
                        "icon",
                        "🧩",
                    ),

                    "triggers": list(
                        getattr(
                            plugin,
                            "triggers",
                            [],
                        )
                        or []
                    ),

                    "capabilities": list(
                        getattr(
                            plugin,
                            "capabilities",
                            [],
                        )
                        or []
                    ),

                    "priority": getattr(
                        plugin,
                        "priority",
                        100,
                    ),

                    "enabled": getattr(
                        plugin,
                        "enabled",
                        True,
                    ),

                    "version": getattr(
                        plugin,
                        "version",
                        "1.0",
                    ),

                    "author": getattr(
                        plugin,
                        "author",
                        "Atlas",
                    ),

                    "has_gui": getattr(
                        plugin,
                        "has_gui",
                        False,
                    ),

                    "gui_id": getattr(
                        plugin,
                        "gui_id",
                        None,
                    ),
                }
            )

        return result

    # ==================================================
    # STATUS
    # ==================================================

    def status(self):
        """
        Return diagnostic information about the tool system.
        """

        plugins = self.plugins.plugins

        enabled = 0
        disabled = 0

        for plugin in plugins.values():

            if getattr(
                plugin,
                "enabled",
                True,
            ):
                enabled += 1
            else:
                disabled += 1

        return {
            "total": len(
                plugins
            ),
            "enabled": enabled,
            "disabled": disabled,
            "tools": self.available(),
        }

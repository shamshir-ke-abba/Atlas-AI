"""
Atlas V3 Tool Manager

Central interface for Atlas tools/plugins.

Responsibilities:
- Load and expose plugins
- Find the best tool for a message
- Execute tools safely
- Provide tool metadata
- Provide diagnostic status
- Keep routing logic out of AtlasBrain
"""

from typing import Any, Optional

from core.plugin_manager import PluginManager
from core.logger import logger


class ToolManager:
    """Central manager for Atlas tools."""

    def __init__(self, profile_store=None):
        self.plugins = PluginManager()

        if profile_store is not None:
            self.attach_profile_store(profile_store)

        logger.info(
            "Available Atlas tools: %s",
            self.available(),
        )

    # ==================================================
    # PROFILE STORE
    # ==================================================

    def attach_profile_store(
        self,
        profile_store,
    ):
        """
        Attach the shared persistent Atlas ProfileStore to
        every plugin that supports profile state.

        This deliberately does not change ToolManager's constructor,
        so existing Atlas code that calls ToolManager() remains compatible.
        """

        self.profile_store = profile_store

        for plugin in self.plugins.plugins.values():

            setter = getattr(
                plugin,
                "set_profile_store",
                None,
            )

            if not callable(setter):
                continue

            try:
                setter(profile_store)

                logger.debug(
                    "ProfileStore attached to tool: %s",
                    getattr(
                        plugin,
                        "name",
                        type(plugin).__name__,
                    ),
                )

            except Exception as exc:
                logger.warning(
                    "Could not attach ProfileStore to tool '%s': %s",
                    getattr(
                        plugin,
                        "name",
                        type(plugin).__name__,
                    ),
                    exc,
                )

    # ==================================================
    # EXECUTION
    # ==================================================

    def execute(
        self,
        name: str,
        **kwargs,
    ) -> Any:
        """
        Execute a registered tool by name.
        """

        if not name:
            raise ValueError(
                "Tool name is required."
            )

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

        logger.info(
            "Executing tool: %s",
            name,
        )

        try:

            return self.plugins.execute(
                name,
                **kwargs,
            )

        except Exception as exc:

            logger.exception(
                "Tool '%s' execution failed: %s",
                name,
                exc,
            )

            raise

    # ==================================================
    # GET
    # ==================================================

    def get(
        self,
        name: str,
    ) -> Optional[Any]:
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

        Each plugin decides whether it can handle the message
        through its can_handle() method.

        Selection order:

        1. Enabled tools only
        2. Tools that can_handle() the message
        3. Lowest priority number wins
        4. Tool name breaks priority ties
        """

        if message is None:
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
            # Check capability
            # ------------------------------------------

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

        # ----------------------------------------------
        # No matching tool
        # ----------------------------------------------

        if not candidates:

            logger.debug(
                "No tool matched message: %s",
                message,
            )

            return None

        # ----------------------------------------------
        # Sort candidates
        # ----------------------------------------------

        candidates.sort(
            key=lambda item: (
                item[0],
                item[1].lower(),
            )
        )

        priority, name, plugin = candidates[0]

        logger.info(
            "Tool match: %s",
            name,
        )

        # ----------------------------------------------
        # Debug competing tools
        # ----------------------------------------------

        if len(candidates) > 1:

            logger.debug(
                "Tool candidates for '%s': %s",
                message,
                [
                    {
                        "name": item[1],
                        "priority": item[0],
                    }
                    for item in candidates
                ],
            )

        return plugin

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
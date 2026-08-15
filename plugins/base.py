"""
Atlas V3 Plugin Base

Base interface for all Atlas plugins/tools.

Responsibilities:
- Define the standard plugin contract
- Provide deterministic message matching
- Provide optional argument extraction
- Provide standardized metadata
- Keep plugins independent from AtlasBrain

This class is intentionally LLM-free.

The plugin system should remain deterministic at this layer.
Higher-level planning/reasoning can be added above it later.
"""

from typing import Any, Dict, Optional


class AtlasPlugin:
    """
    Base class for every Atlas plugin/tool.

    Required:
        name
        description
        can_handle()
        run()

    Optional:
        extract_arguments()

    Metadata fields provide a consistent interface for
    ToolManager, future planners, Skills, and GUI systems.
    """

    # ==========================================================
    # IDENTITY
    # ==========================================================

    name = "unknown"

    display_name = "Atlas Plugin"

    description = "Atlas plugin"

    version = "1.0"

    author = "Atlas"

    # ==========================================================
    # UI
    # ==========================================================

    icon = "🧩"

    has_gui = False

    gui_id = None

    # ==========================================================
    # ROUTING
    # ==========================================================

    triggers = []

    capabilities = []

    # Lower number = higher priority.
    priority = 100

    # Plugin can be disabled without being unloaded.
    enabled = True

    # ==========================================================
    # MATCHING
    # ==========================================================

    def can_handle(
        self,
        message: str,
    ) -> bool:
        """
        Determine whether this plugin can handle a message.

        Plugins should override this method.

        Requirements:
        - Must be deterministic.
        - Must not call the LLM.
        - Must not execute the tool.
        - Should return True/False only.
        """

        return False

    # ==========================================================
    # ARGUMENT EXTRACTION
    # ==========================================================

    def extract_arguments(
        self,
        message: str,
    ) -> Dict[str, Any]:
        """
        Extract structured arguments from a user message.

        Example:

            User:
                "Calculate 25 * 4"

            Returns:

                {
                    "expression": "25 * 4"
                }

        Plugins may override this when they need structured
        arguments.

        The default implementation preserves the raw message.
        """

        return {
            "message": message
        }

    # ==========================================================
    # PROFILE STORE
    # ==========================================================

    def set_profile_store(
        self,
        profile_store,
    ):
        """
        Attach Atlas's shared persistent profile store.

        Profile-aware plugins can use self.profile_store.
        Other plugins may safely ignore it.
        """

        self.profile_store = profile_store

    # ==========================================================
    # EXECUTION
    # ==========================================================

    def run(
        self,
        message: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Execute the plugin.

        Every executable plugin MUST override this method.
        """

        raise NotImplementedError(
            f"Plugin '{self.name}' "
            "does not implement run()."
        )

    # ==========================================================
    # METADATA
    # ==========================================================

    def info(self) -> Dict[str, Any]:
        """
        Return standardized plugin metadata.

        ToolManager and future planner/skills systems can use
        this without knowing the concrete plugin class.
        """

        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "icon": self.icon,
            "triggers": list(self.triggers or []),
            "capabilities": list(
                self.capabilities or []
            ),
            "priority": self.priority,
            "enabled": self.enabled,
            "has_gui": self.has_gui,
            "gui_id": self.gui_id,
        }

    # ==========================================================
    # STATUS
    # ==========================================================

    def is_enabled(self) -> bool:
        """
        Return whether this plugin is currently enabled.
        """

        return bool(
            self.enabled
        )

    # ==========================================================
    # REPRESENTATION
    # ==========================================================

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"name='{self.name}'>"
        )
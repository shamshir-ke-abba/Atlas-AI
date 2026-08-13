"""
Atlas V3 Plugin Base

Base interface for all Atlas plugins/tools.

Responsibilities:
- Define the standard plugin interface
- Provide deterministic message matching
- Provide optional argument extraction
- Keep plugins independent from AtlasBrain
"""

from typing import Any, Dict, Optional


class AtlasPlugin:
    """
    Base class for every Atlas plugin.

    Plugins should implement:

        name
        description
        can_handle()
        run()

    Optional:

        extract_arguments()
    """

    # ==========================================================
    # METADATA
    # ==========================================================

    name = "unknown"

    description = (
        "Atlas plugin"
    )

    # ==========================================================
    # MATCHING
    # ==========================================================

    def can_handle(
        self,
        message: str,
    ) -> bool:
        """
        Determine whether this plugin can handle a message.

        Plugins should override this with deterministic logic.

        This method MUST NOT call the LLM.
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

        The default implementation returns the raw message.
        """

        return {
            "message": message
        }

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

        Plugins MUST override this.
        """

        raise NotImplementedError(
            f"Plugin '{self.name}' "
            "does not implement run()."
        )

    # ==========================================================
    # INFO
    # ==========================================================

    def info(self) -> Dict[str, Any]:
        """
        Return plugin metadata.

        Used by the tool system and future planner.
        """

        return {
            "name": self.name,
            "description": self.description,
        }

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"name='{self.name}'>"
        )
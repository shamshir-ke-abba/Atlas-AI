"""
Atlas V3 Planner

Determines whether a request should be handled
by a deterministic plugin or the local model.

Responsibilities:
- Ask IntentRouter for the best plugin
- Extract plugin arguments
- Detect math operations
- Detect math variables
- Produce a deterministic Plan

The Planner NEVER executes plugins.
"""


from dataclasses import dataclass


@dataclass
class Plan:
    """Represents Atlas's deterministic execution plan."""

    action: str

    plugin: object = None

    arguments: str = ""

    operation: str = ""

    variable: str = "x"


class Planner:

    DIRECT = "direct"

    TOOL = "tool"

    def __init__(self, router):

        self.router = router

    # =========================================================
    # PLAN
    # =========================================================

    def plan(
        self,
        message,
    ):
        """
        Build a deterministic execution plan.

        Flow:

            User message
                  ↓
            IntentRouter.match()
                  ↓
               Plugin
                  ↓
          extract_arguments()
                  ↓
                Plan
        """

        message = str(
            message or ""
        ).strip()

        if not message:

            return Plan(
                action=self.DIRECT
            )

        # -----------------------------------------------------
        # Find plugin
        # -----------------------------------------------------

        plugin = self.router.match(
            message
        )

        if plugin is None:

            return Plan(
                action=self.DIRECT
            )

        # -----------------------------------------------------
        # Extract arguments
        # -----------------------------------------------------

        arguments = (
            self.router.extract_arguments(
                plugin,
                message,
            )
        )

        # -----------------------------------------------------
        # Specialized plugin arguments
        # -----------------------------------------------------

        if isinstance(
            arguments,
            dict,
        ):

            raw_arguments = (
                arguments.get(
                    "expression",
                    arguments.get(
                        "message",
                        "",
                    ),
                )
            )

            arguments = str(
                raw_arguments or ""
            ).strip()

        else:

            arguments = str(
                arguments or ""
            ).strip()

        # -----------------------------------------------------
        # Operation
        # -----------------------------------------------------

        operation = ""

        # -----------------------------------------------------
        # Variable
        # -----------------------------------------------------

        variable = "x"

        # =====================================================
        # MATH PLUGIN
        # =====================================================

        if getattr(
            plugin,
            "name",
            "",
        ) == "math":

            # -------------------------------------------------
            # Detect mathematical operation
            # -------------------------------------------------

            if hasattr(
                plugin,
                "detect_operation",
            ):

                try:

                    detected_operation = (
                        plugin.detect_operation(
                            message
                        )
                    )

                    if detected_operation:

                        operation = str(
                            detected_operation
                        ).strip()

                except Exception:
                    operation = ""

            # -------------------------------------------------
            # Detect variable
            # -------------------------------------------------

            if hasattr(
                plugin,
                "detect_variable",
            ):

                try:

                    detected_variable = (
                        plugin.detect_variable(
                            message,
                            arguments,
                        )
                    )

                    if detected_variable:

                        variable = str(
                            detected_variable
                        ).strip()

                except Exception:
                    variable = "x"

        # -----------------------------------------------------
        # Return plan
        # -----------------------------------------------------

        return Plan(
            action=self.TOOL,
            plugin=plugin,
            arguments=arguments,
            operation=operation,
            variable=variable,
        )
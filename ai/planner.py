"""
Atlas Planner

Decides what Atlas should do with a user request.
"""

from dataclasses import dataclass


@dataclass
class Plan:

    action: str

    plugin: object = None

    arguments: str = ""


class Planner:

    DIRECT = "direct"

    TOOL = "tool"

    def __init__(
        self,
        router,
    ):

        self.router = router

    def plan(
        self,
        message,
    ):

        plugin = self.router.match(
            message
        )

        if plugin:

            arguments = (
                self.router.extract_arguments(
                    plugin,
                    message,
                )
            )

            return Plan(
                action=self.TOOL,
                plugin=plugin,
                arguments=arguments,
            )

        return Plan(
            action=self.DIRECT
        )
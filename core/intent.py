"""
Atlas V3 Intent Router
"""


class IntentRouter:

    def __init__(self, plugins):
        self.plugins = plugins

    def match(self, message):

        text = message.lower().strip()

        best_plugin = None
        best_score = 0

        for plugin in self.plugins.values():

            if not plugin.enabled:
                continue

            if not plugin.can_handle(message):
                continue

            trigger_score = 0

            for trigger in plugin.triggers:

                trigger = trigger.lower().strip()

                if not trigger:
                    continue

                # Exact command
                if text == trigger:
                    trigger_score = max(
                        trigger_score,
                        1000,
                    )

                # Command followed by arguments
                elif text.startswith(
                    trigger + " "
                ):
                    trigger_score = max(
                        trigger_score,
                        100,
                    )

                # Trigger appears as a complete word/phrase
                elif (
                    f" {trigger} "
                    in f" {text} "
                ):
                    trigger_score = max(
                        trigger_score,
                        len(trigger),
                    )

            # IMPORTANT:
            # No trigger match = plugin does not match.
            if trigger_score == 0:
                continue

            score = (
                trigger_score
                + plugin.priority
            )

            if score > best_score:

                best_score = score
                best_plugin = plugin

        return best_plugin

    def extract_arguments(
        self,
        plugin,
        message,
    ):

        expression = message.strip()

        for trigger in sorted(
            plugin.triggers,
            key=len,
            reverse=True,
        ):

            trigger_lower = trigger.lower()

            if expression.lower().startswith(
                trigger_lower
            ):

                expression = expression[
                    len(trigger):
                ].strip()

                break

        return expression.rstrip(
            "?!.,;:"
        ).strip()
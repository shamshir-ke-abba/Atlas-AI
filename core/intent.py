"""
Atlas V3 Intent Router

Deterministically selects the best plugin for a message.

Responsibilities:
- Select the best enabled plugin
- Score plugin matches
- Extract clean plugin arguments
- Never execute plugins
"""

import re


class IntentRouter:

    def __init__(self, plugins):
        self.plugins = plugins

    # =========================================================
    # MATCH
    # =========================================================

    def match(self, message):

        text = (
            str(message or "")
            .lower()
            .strip()
        )

        if not text:
            return None

        candidates = []

        for plugin in self.plugins.values():

            if not getattr(
                plugin,
                "enabled",
                True,
            ):
                continue

            try:
                if not plugin.can_handle(message):
                    continue

            except Exception:
                continue

            score = self._score(
                plugin,
                text,
            )

            if score <= 0:
                continue

            priority = getattr(
                plugin,
                "priority",
                100,
            )

            try:
                priority = int(priority)

            except (
                TypeError,
                ValueError,
            ):
                priority = 100

            candidates.append(
                (
                    score,
                    priority,
                    str(
                        getattr(
                            plugin,
                            "name",
                            "",
                        )
                    ).lower(),
                    plugin,
                )
            )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: (
                -item[0],
                item[1],
                item[2],
            )
        )

        return candidates[0][3]

    # =========================================================
    # SCORE
    # =========================================================

    def _score(
        self,
        plugin,
        text,
    ):

        best = 0

        triggers = getattr(
            plugin,
            "triggers",
            [],
        ) or []

        for trigger in triggers:

            trigger = (
                str(trigger)
                .lower()
                .strip()
            )

            if not trigger:
                continue

            # Exact trigger
            if text == trigger:

                best = max(
                    best,
                    1000 + len(trigger),
                )

                continue

            # Trigger followed by arguments
            if text.startswith(
                trigger + " "
            ):

                best = max(
                    best,
                    700 + len(trigger),
                )

                continue

            # Complete phrase inside message
            padded = f" {text} "

            if f" {trigger} " in padded:

                best = max(
                    best,
                    300 + len(trigger),
                )

        return best

    # =========================================================
    # ARGUMENT EXTRACTION
    # =========================================================

    def extract_arguments(
        self,
        plugin,
        message,
    ):
        """
        Extract arguments for a plugin.

        Examples:

            "What time is it?"
                -> ""

            "calculate 25 * 37"
                -> "25 * 37"

            "calc 100 / 4"
                -> "100 / 4"

            "time"
                -> ""

        Plugin-specific extractors are supported, but generic
        AtlasPlugin extraction must not override deterministic
        argument cleanup.
        """

        original = str(
            message or ""
        ).strip()

        if not original:
            return ""

        # -----------------------------------------------------
        # Normalize punctuation for matching.
        #
        # Keep the original casing for returned arguments.
        # -----------------------------------------------------

        text = original.rstrip(
            "?!.,;:"
        ).strip()

        lowered = text.lower()

        # -----------------------------------------------------
        # Plugin name
        # -----------------------------------------------------

        plugin_name = str(
            getattr(
                plugin,
                "name",
                "",
            )
        ).lower()

        # =====================================================
        # TIME / DATE
        # =====================================================

        if plugin_name == "time":

            return ""

        # =====================================================
        # CALCULATOR
        # =====================================================

        if plugin_name == "calculator":

            return self._extract_calculator_expression(
                text
            )

        # =====================================================
        # PLUGIN-SPECIFIC EXTRACTOR
        # =====================================================

        extractor = getattr(
            plugin,
            "extract_arguments",
            None,
        )

        if callable(extractor):

            try:

                result = extractor(
                    original
                )

                # ---------------------------------------------
                # Structured plugin arguments
                # ---------------------------------------------

                if isinstance(
                    result,
                    dict,
                ):

                    # A generic {"message": original_message}
                    # is NOT useful as extracted arguments.
                    #
                    # Only return meaningful structured data.
                    if (
                        "message" in result
                        and len(result) == 1
                    ):

                        extracted_message = str(
                            result.get(
                                "message",
                                "",
                            )
                        ).strip()

                        # If the plugin simply echoed the
                        # original request, continue with
                        # generic extraction instead.
                        if (
                            extracted_message.lower()
                            == lowered
                        ):
                            pass

                        else:
                            return result

                    else:

                        return result

                # ---------------------------------------------
                # Normal string result
                # ---------------------------------------------

                elif result is not None:

                    result = str(
                        result
                    ).strip()

                    if result:
                        return result

            except Exception:
                pass

        # =====================================================
        # GENERIC TRIGGER EXTRACTION
        # =====================================================

        triggers = getattr(
            plugin,
            "triggers",
            [],
        ) or []

        normalized_triggers = []

        for trigger in triggers:

            trigger = (
                str(trigger)
                .strip()
            )

            if trigger:
                normalized_triggers.append(
                    trigger
                )

        # Longest trigger first so that:

        # "what is the time"

        # wins over:

        # "what"

        normalized_triggers.sort(
            key=len,
            reverse=True,
        )

        # -----------------------------------------------------
        # Exact trigger
        # -----------------------------------------------------

        for trigger in normalized_triggers:

            if (
                lowered
                == trigger.lower()
            ):

                return ""

        # -----------------------------------------------------
        # Trigger + arguments
        # -----------------------------------------------------

        for trigger in normalized_triggers:

            trigger_lower = (
                trigger.lower()
            )

            if lowered.startswith(
                trigger_lower + " "
            ):

                return text[
                    len(trigger):
                ].strip()

        # -----------------------------------------------------
        # Default
        # -----------------------------------------------------

        return text

    # =========================================================
    # CALCULATOR EXTRACTION
    # =========================================================

    def _extract_calculator_expression(
        self,
        text,
    ):
        """
        Convert natural-language calculator commands
        into a clean arithmetic expression.
        """

        text = str(
            text or ""
        ).strip()

        if not text:
            return ""

        lowered = text.lower()

        prefixes = (
            "calculate",
            "calc",
            "compute",
            "evaluate",
            "what is",
            "what's",
        )

        # -----------------------------------------------------
        # Explicit calculator command
        # -----------------------------------------------------

        for prefix in prefixes:

            if lowered == prefix:

                return ""

            if lowered.startswith(
                prefix + " "
            ):

                return text[
                    len(prefix):
                ].strip()

        # -----------------------------------------------------
        # Already a raw arithmetic expression
        # -----------------------------------------------------

        if re.fullmatch(
            r"[0-9eEpiPI+\-*/%^().\s]+",
            text,
        ):

            return text

        # -----------------------------------------------------
        # If calculator somehow matched a natural-language
        # expression without one of the known prefixes,
        # return the text rather than destroying information.
        # -----------------------------------------------------

        return text
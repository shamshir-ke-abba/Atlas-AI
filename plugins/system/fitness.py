"""
Atlas Fitness Planner Plugin
"""

import json

from config import DATA_DIR
from plugins.base import AtlasPlugin


class FitnessPlugin(AtlasPlugin):

    name = "fitness"

    display_name = "Fitness Planner"

    description = (
        "Creates and manages basic fitness profiles, "
        "exercise suggestions, and workout plans."
    )

    icon = "🏋️"

    has_gui = True

    gui_id = "fitness"

    triggers = [
        "fitness",
        "workout",
        "exercise",
        "gym",
    ]

    # ==================================================
    # Initialization
    # ==================================================

    def __init__(self):

        super().__init__()

        self.profile_file = (
            DATA_DIR / "fitness_profile.json"
        )

        self.profile = (
            self._load_profile()
        )

    # ==================================================
    # Profile
    # ==================================================

    def _load_profile(self):

        if self.profile_file.exists():

            try:

                with self.profile_file.open(
                    "r",
                    encoding="utf-8",
                ) as file:

                    return json.load(file)

            except Exception:
                pass

        return {
            "experience": "beginner",
            "goal": None,
            "equipment": [],
            "restrictions": [],
        }

    def _save_profile(self):

        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.profile_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self.profile,
                file,
                indent=2,
            )

    # ==================================================
    # Can Handle
    # ==================================================

    def can_handle(
        self,
        message,
    ):

        text = str(
            message
        ).lower().strip()

        for trigger in self.triggers:

            if text == trigger:
                return True

            if text.startswith(
                trigger + " "
            ):

                return True

        return False

    # ==================================================
    # Run
    # ==================================================

    def run(
        self,
        action="",
        **kwargs,
    ):

        action = str(
            action
        ).lower().strip()

        if action == "set_profile":

            return self.set_profile(
                **kwargs
            )

        if action == "get_exercises":

            return self.get_exercises(
                kwargs.get(
                    "muscle_group"
                )
            )

        if action == "generate_workout":

            return self.generate_workout(
                **kwargs
            )

        return (
            "Fitness Planner\n\n"
            "Available actions:\n"
            "• set_profile\n"
            "• get_exercises\n"
            "• generate_workout"
        )

    # ==================================================
    # Set Profile
    # ==================================================

    def set_profile(
        self,
        experience=None,
        goal=None,
        equipment=None,
        restrictions=None,
    ):

        if experience is not None:
            self.profile[
                "experience"
            ] = experience

        if goal is not None:
            self.profile[
                "goal"
            ] = goal

        if equipment is not None:
            self.profile[
                "equipment"
            ] = equipment

        if restrictions is not None:
            self.profile[
                "restrictions"
            ] = restrictions

        self._save_profile()

        return (
            "Fitness profile updated."
        )

    # ==================================================
    # Exercises
    # ==================================================

    def get_exercises(
        self,
        muscle_group=None,
    ):

        exercises = {
            "chest": [
                "bench press",
                "incline press",
                "dips",
            ],
            "back": [
                "pull-ups",
                "rows",
                "lat pulldown",
            ],
            "shoulders": [
                "overhead press",
                "lateral raises",
                "shrugs",
            ],
            "legs": [
                "squats",
                "deadlifts",
                "leg press",
            ],
        }

        if not muscle_group:

            return (
                "Available muscle groups:\n"
                + "\n".join(
                    f"• {group}"
                    for group in exercises
                )
            )

        group = str(
            muscle_group
        ).lower().strip()

        group_exercises = (
            exercises.get(
                group
            )
        )

        if not group_exercises:

            return (
                f"No exercise list available "
                f"for '{muscle_group}'."
            )

        return (
            f"{group.title()} exercises:\n\n"
            + "\n".join(
                f"• {exercise}"
                for exercise in group_exercises
            )
        )

    # ==================================================
    # Workout
    # ==================================================

    def generate_workout(
        self,
        frequency=3,
        **kwargs,
    ):

        return (
            f"Generated a {frequency}x/week "
            "workout based on the current "
            "fitness profile."
        )
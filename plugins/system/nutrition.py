"""
Atlas Nutrition Planner Plugin
"""

import json

from config import DATA_DIR
from plugins.base import AtlasPlugin


class NutritionPlugin(AtlasPlugin):

    name = "nutrition"

    display_name = "Nutrition Planner"

    description = (
        "Stores nutrition preferences and "
        "creates basic meal schedules."
    )

    icon = "🥗"

    has_gui = True

    gui_id = "nutrition"

    triggers = [
        "nutrition",
        "diet",
        "meal",
        "meals",
        "food",
    ]

    # ==================================================
    # Initialization
    # ==================================================

    def __init__(self):

        super().__init__()

        self.profile_file = (
            DATA_DIR / "nutrition_profile.json"
        )

        self.meals_file = (
            DATA_DIR / "meal_plan.json"
        )

        self.profile = (
            self._load_profile()
        )

        self.meals = (
            self._load_meals()
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
            "age": None,
            "height": None,
            "weight": None,
            "activity_level": "moderate",
            "diet_pattern": "balanced",
            "allergies": [],
            "intolerances": [],
            "preferences": [],
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
    # Meals
    # ==================================================

    def _load_meals(self):

        if self.meals_file.exists():

            try:

                with self.meals_file.open(
                    "r",
                    encoding="utf-8",
                ) as file:

                    return json.load(file)

            except Exception:
                pass

        return {}

    def _save_meals(self):

        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.meals_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self.meals,
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

        if action == "generate_meal_plan":

            return self.generate_meal_plan(
                **kwargs
            )

        if action == "get_meal_plan":

            return self.get_meal_plan()

        return (
            "Nutrition Planner\n\n"
            "Available actions:\n"
            "• set_profile\n"
            "• generate_meal_plan\n"
            "• get_meal_plan"
        )

    # ==================================================
    # Set Profile
    # ==================================================

    def set_profile(
        self,
        **kwargs,
    ):

        for key, value in kwargs.items():

            if key in self.profile:

                self.profile[
                    key
                ] = value

        self._save_profile()

        return (
            "Nutrition profile updated."
        )

    # ==================================================
    # Generate Meal Plan
    # ==================================================

    def generate_meal_plan(
        self,
        meals_per_day=3,
        **kwargs,
    ):

        plan = {
            "08:00": (
                "Breakfast — "
                "Balanced carbohydrates + protein"
            ),

            "12:00": (
                "Lunch — "
                "Whole grains + vegetables + protein"
            ),

            "17:00": (
                "Snack — "
                "Fruit + nuts"
            ),

            "20:00": (
                "Dinner — "
                "Vegetables + protein"
            ),
        }

        self.meals = plan

        self._save_meals()

        result = (
            "Meal plan generated:\n\n"
        )

        for time, meal in plan.items():

            result += (
                f"{time}  {meal}\n"
            )

        return result

    # ==================================================
    # Get Meal Plan
    # ==================================================

    def get_meal_plan(self):

        if not self.meals:

            return (
                "No meal plan has been "
                "created yet."
            )

        result = (
            "Current meal plan:\n\n"
        )

        for time, meal in self.meals.items():

            result += (
                f"{time}  {meal}\n"
            )

        return result
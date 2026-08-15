"""Atlas Nutrition Planner.

Uses the central Atlas ProfileStore as the single source of truth.
The legacy nutrition_profile.json is supported as a migration source.
"""

import json

from config import DATA_DIR
from plugins.base import AtlasPlugin


class NutritionPlugin(AtlasPlugin):
    name = "nutrition"
    display_name = "Nutrition Planner"
    description = "Builds profile-aware meal schedules and stores food preferences."
    icon = "🥗"
    has_gui = True
    gui_id = "nutrition"
    priority = 11

    triggers = [
        "nutrition",
        "diet",
        "meal",
        "meals",
        "food",
        "meal plan",
        "mealplan",
    ]

    def __init__(self):
        super().__init__()

        self.profile_file = DATA_DIR / "nutrition_profile.json"
        self.meals_file = DATA_DIR / "meal_plan.json"

        self.profile = self._load_legacy_profile()
        self.meals = self._load_meals()

        self.profile_store = None

    # ==========================================================
    # PROFILE STORE
    # ==========================================================

    def set_profile_store(self, profile_store):
        """Receive the central Atlas ProfileStore."""

        self.profile_store = profile_store

        self._migrate_legacy_profile()
        self._refresh_profile()

    def _refresh_profile(self):
        """Refresh the compatibility profile from central storage."""

        if self.profile_store is None:
            return self.profile

        nutrition = (
            self.profile_store.get(
                "nutrition",
                {},
            )
            or {}
        )

        self.profile = {
            "name": self.profile_store.get(
                "identity.name"
            ),
            "age": self.profile_store.get(
                "identity.age"
            ),
            "activity_level": self.profile_store.get(
                "schedule.activity_level"
            ),
            "diet_pattern": (
                nutrition.get("diet")
                or "balanced"
            ),
            "allergies": nutrition.get(
                "allergies",
                [],
            ),
            "intolerances": nutrition.get(
                "intolerances",
                [],
            ),
            "preferences": nutrition.get(
                "preferences",
                [],
            ),
        }

        return self.profile

    def _migrate_legacy_profile(self):
        """Migrate an existing nutrition profile into ProfileStore."""

        if self.profile_store is None:
            return

        nutrition = (
            self.profile_store.get(
                "nutrition",
                {},
            )
            or {}
        )

        legacy = self.profile

        values = {}

        mapping = {
            "diet_pattern": "diet",
            "allergies": "allergies",
            "intolerances": "intolerances",
            "preferences": "preferences",
        }

        for old_key, new_key in mapping.items():

            value = legacy.get(old_key)

            if value not in (
                None,
                "",
                [],
            ):

                current = nutrition.get(
                    new_key
                )

                # Do not overwrite a profile already
                # stored centrally.
                if current in (
                    None,
                    "",
                    [],
                    "balanced",
                ):
                    values[new_key] = value

        if values:
            self.profile_store.update_section(
                "nutrition",
                values,
            )

        if not self.profile_store.get(
            "identity.name"
        ):
            if legacy.get("name"):
                self.profile_store.set(
                    "identity.name",
                    legacy["name"],
                )

        if not self.profile_store.get(
            "identity.age"
        ):
            if legacy.get("age"):
                self.profile_store.set(
                    "identity.age",
                    legacy["age"],
                )

        if not self.profile_store.get(
            "schedule.activity_level"
        ):
            if legacy.get("activity_level"):
                self.profile_store.set(
                    "schedule.activity_level",
                    legacy["activity_level"],
                )

    # ==========================================================
    # LEGACY STORAGE
    # ==========================================================

    def _load_legacy_profile(self):
        default = {
            "name": None,
            "age": None,
            "activity_level": None,
            "diet_pattern": "balanced",
            "allergies": [],
            "intolerances": [],
            "preferences": [],
        }

        if self.profile_file.exists():
            try:
                data = json.loads(
                    self.profile_file.read_text(
                        encoding="utf-8"
                    )
                )

                if isinstance(data, dict):
                    default.update(data)

            except Exception:
                pass

        return default

    def _save_legacy_profile(self):
        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.profile_file.write_text(
            json.dumps(
                self.profile,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def _load_meals(self):
        if self.meals_file.exists():
            try:
                data = json.loads(
                    self.meals_file.read_text(
                        encoding="utf-8"
                    )
                )

                if isinstance(data, dict):
                    return data

            except Exception:
                pass

        return {}

    def _save_meals(self):
        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.meals_file.write_text(
            json.dumps(
                self.meals,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    # ==========================================================
    # PROFILE
    # ==========================================================

    def profile_complete(self):
        self._refresh_profile()

        return bool(
            self.profile.get("activity_level")
            or self.profile.get("diet_pattern")
        )

    def set_profile(self, **kwargs):
        """Save nutrition information into central Atlas memory."""

        allowed = {
            "name",
            "age",
            "activity_level",
            "diet_pattern",
            "allergies",
            "intolerances",
            "preferences",
        }

        values = {
            key: value
            for key, value in kwargs.items()
            if key in allowed
            and value not in (
                None,
                "",
                [],
            )
        }

        if self.profile_store is not None:

            nutrition_values = {}

            if "diet_pattern" in values:
                nutrition_values["diet"] = values[
                    "diet_pattern"
                ]

            for key in (
                "allergies",
                "intolerances",
                "preferences",
            ):
                if key in values:
                    nutrition_values[key] = values[key]

            if nutrition_values:
                self.profile_store.update_section(
                    "nutrition",
                    nutrition_values,
                )

            if "name" in values:
                self.profile_store.set(
                    "identity.name",
                    values["name"],
                )

            if "age" in values:
                self.profile_store.set(
                    "identity.age",
                    values["age"],
                )

            if "activity_level" in values:
                self.profile_store.set(
                    "schedule.activity_level",
                    values["activity_level"],
                )

            self._refresh_profile()

        else:
            self.profile.update(values)
            self._save_legacy_profile()

        return (
            "Nutrition profile saved to Atlas memory. "
            "Future meal-plan requests can use it."
        )

    def get_profile(self):
        self._refresh_profile()

        return (
            "Nutrition profile:\n"
            + "\n".join(
                f"• {k.replace('_', ' ').title()}: "
                f"{v if v not in (None, '', [], {}) else 'Not set'}"
                for k, v in self.profile.items()
            )
        )

    # ==========================================================
    # ROUTING
    # ==========================================================

    def can_handle(self, message):
        text = str(
            message or ""
        ).lower().strip()

        if not text:
            return False

        if any(
            text == trigger
            or text.startswith(trigger + " ")
            for trigger in self.triggers
        ):
            return True

        return any(
            phrase in text
            for phrase in (
                "make me a meal plan",
                "generate a meal plan",
                "what should i eat",
                "my diet",
                "my meals",
                "meal schedule",
                "food plan",
                "nutrition profile",
                "current meal plan",
                "show my meal plan",
                "what is my meal plan",
            )
        )

    def _infer_action(self, message):
        text = str(
            message or ""
        ).lower()

        if "profile" in text:
            return "get_profile"

        if any(
            phrase in text
            for phrase in (
                "current meal plan",
                "show my meal plan",
                "what is my meal plan",
            )
        ):
            return "get_meal_plan"

        if any(
            phrase in text
            for phrase in (
                "meal plan",
                "meal schedule",
                "what should i eat",
                "generate meals",
            )
        ):
            return "generate_meal_plan"

        return "help"

    def run(self, action="", message="", **kwargs):
        action = str(
            action or ""
        ).lower().strip()

        message = str(
            message
            or kwargs.pop("prompt", "")
            or ""
        )

        if not action:
            action = self._infer_action(message)

        if action == "set_profile":
            return self.set_profile(**kwargs)

        if action == "get_profile":
            return self.get_profile()

        if action == "generate_meal_plan":
            return self.generate_meal_plan(
                meals_per_day=kwargs.get(
                    "meals_per_day",
                    4,
                )
            )

        if action == "get_meal_plan":
            return self.get_meal_plan()

        return (
            "I can use your saved nutrition profile "
            "to create a general meal schedule or "
            "show your saved plan."
        )

    # ==========================================================
    # MEAL GENERATION
    # ==========================================================

    def generate_meal_plan(
        self,
        meals_per_day=4,
        **kwargs,
    ):
        self._refresh_profile()

        try:
            meals_per_day = max(
                3,
                min(
                    int(meals_per_day),
                    6,
                ),
            )
        except Exception:
            meals_per_day = 4

        diet = (
            self.profile.get("diet_pattern")
            or "balanced"
        )

        allergies = (
            self.profile.get("allergies")
            or []
        )

        intolerances = (
            self.profile.get("intolerances")
            or []
        )

        preferences = (
            self.profile.get("preferences")
            or []
        )

        if not isinstance(
            allergies,
            list,
        ):
            allergies = [str(allergies)]

        if not isinstance(
            intolerances,
            list,
        ):
            intolerances = [
                str(intolerances)
            ]

        if not isinstance(
            preferences,
            list,
        ):
            preferences = [
                str(preferences)
            ]

        # Build descriptions from the saved profile.
        if diet.lower() in (
            "vegetarian",
            "veg",
        ):
            breakfast = (
                "a vegetarian breakfast with "
                "a grain, protein-rich food and fruit"
            )
            lunch = (
                "a vegetarian meal with grains, "
                "lentils/beans or another protein source "
                "and vegetables"
            )
            dinner = (
                "a balanced vegetarian dinner with "
                "vegetables, grains/starch and protein"
            )

        elif diet.lower() in (
            "vegan",
        ):
            breakfast = (
                "a plant-based breakfast with "
                "whole grains, beans/nut-based protein "
                "and fruit"
            )
            lunch = (
                "a plant-based meal with grains, "
                "beans/lentils and vegetables"
            )
            dinner = (
                "a balanced plant-based dinner with "
                "vegetables, grains/starch and protein"
            )

        else:
            breakfast = (
                "a balanced breakfast with "
                "a carbohydrate, protein and fruit/vegetable"
            )
            lunch = (
                "a balanced meal with grains/starch, "
                "protein and vegetables"
            )
            dinner = (
                "a balanced dinner with vegetables, "
                "carbohydrate and protein"
            )

        snack = (
            "a suitable snack such as fruit, yogurt, "
            "nuts/seeds or another preferred option"
        )

        plan = [
            (
                "08:00",
                "Breakfast",
                breakfast,
            ),
            (
                "12:00",
                "Lunch",
                lunch,
            ),
            (
                "17:00",
                "Snack",
                snack,
            ),
            (
                "20:00",
                "Dinner",
                dinner,
            ),
        ]

        if meals_per_day >= 5:
            plan.insert(
                3,
                (
                    "15:00",
                    "Snack",
                    "a simple snack matching "
                    "your saved preferences",
                ),
            )

        if meals_per_day >= 6:
            plan.insert(
                4,
                (
                    "18:00",
                    "Snack",
                    "another suitable snack "
                    "based on your preferences",
                ),
            )

        plan = plan[:meals_per_day]

        self.meals = {
            time: (
                f"{label} — {description}"
            )
            for time, label, description in plan
        }

        self._save_meals()

        lines = [
            "Meal plan generated from your saved profile:",
            "",
            f"Diet pattern: {diet}",
        ]

        if preferences:
            lines.append(
                "Preferences: "
                + ", ".join(
                    map(str, preferences)
                )
            )

        lines.append("")

        lines.extend(
            f"**{time}**  {meal}"
            for time, meal in self.meals.items()
        )

        if allergies:
            lines.extend(
                [
                    "",
                    "Allergies to avoid: "
                    + ", ".join(
                        map(str, allergies)
                    ),
                ]
            )

        if intolerances:
            lines.append(
                "Intolerances to consider: "
                + ", ".join(
                    map(str, intolerances)
                )
            )

        lines.extend(
            [
                "",
                "This is general meal-planning guidance, "
                "not medical advice. If you have allergies, "
                "medical dietary needs, or other restrictions, "
                "check the plan with a parent/guardian or "
                "qualified healthcare professional.",
            ]
        )

        return "\n".join(lines)

    # ==========================================================
    # SAVED PLAN
    # ==========================================================

    def get_meal_plan(self):
        if not self.meals:
            return (
                "No meal plan has been created yet. "
                "Ask me to generate one."
            )

        return (
            "Current meal plan:\n\n"
            + "\n".join(
                f"**{time}**  {meal}"
                for time, meal in self.meals.items()
            )
        )

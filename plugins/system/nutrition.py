"""Atlas Nutrition Planner plugin.

The backend owns profile storage and meal-plan generation. The GUI is only a
client; the same actions are available through Atlas chat/tool routing.
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

    triggers = ["nutrition", "diet", "meal", "meals", "food", "meal plan", "mealplan"]

    def __init__(self):
        super().__init__()
        self.profile_file = DATA_DIR / "nutrition_profile.json"
        self.meals_file = DATA_DIR / "meal_plan.json"
        self.profile = self._load_profile()
        self.meals = self._load_meals()

    def _load_profile(self):
        default = {
            "name": None, "age": None, "activity_level": None,
            "diet_pattern": "balanced", "allergies": [],
            "intolerances": [], "preferences": [],
        }
        if self.profile_file.exists():
            try:
                default.update(json.loads(self.profile_file.read_text(encoding="utf-8")))
            except Exception:
                pass
        return default

    def _load_meals(self):
        if self.meals_file.exists():
            try:
                return json.loads(self.meals_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_profile(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.profile_file.write_text(json.dumps(self.profile, indent=2, ensure_ascii=False), encoding="utf-8")

    def _save_meals(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.meals_file.write_text(json.dumps(self.meals, indent=2, ensure_ascii=False), encoding="utf-8")

    def profile_complete(self):
        return bool(self.profile.get("age") and self.profile.get("activity_level"))

    def can_handle(self, message):
        text = str(message or "").lower().strip()
        if not text:
            return False
        if any(text == t or text.startswith(t + " ") for t in self.triggers):
            return True
        return any(p in text for p in (
            "make me a meal plan", "generate a meal plan", "what should i eat",
            "my diet", "my meals", "meal schedule", "food plan",
        ))

    def _infer_action(self, message):
        text = str(message or "").lower()
        if any(p in text for p in ("current meal plan", "show my meal plan", "what is my meal plan")):
            return "get_meal_plan"
        if any(p in text for p in ("meal plan", "meal schedule", "what should i eat", "generate meals")):
            return "generate_meal_plan"
        if "profile" in text:
            return "get_profile"
        return "help"

    def run(self, action="", message="", **kwargs):
        action = str(action or "").lower().strip()
        message = str(message or kwargs.pop("prompt", "") or "")
        if not action:
            action = self._infer_action(message)
        if action == "set_profile":
            return self.set_profile(**kwargs)
        if action == "get_profile":
            return self.get_profile()
        if action == "generate_meal_plan":
            return self.generate_meal_plan(meals_per_day=kwargs.get("meals_per_day", 4))
        if action == "get_meal_plan":
            return self.get_meal_plan()
        return "I can use your nutrition profile to create a simple meal schedule or show your saved plan."

    def set_profile(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.profile and value not in (None, "", []):
                self.profile[key] = value
        self._save_profile()
        return "Nutrition profile saved. Atlas can now use it for future meal-plan requests."

    def get_profile(self):
        return "Nutrition profile:\n" + "\n".join(
            f"• {k.replace('_', ' ').title()}: {v or 'Not set'}"
            for k, v in self.profile.items()
        )

    def generate_meal_plan(self, meals_per_day=4, **kwargs):
        try:
            meals_per_day = max(3, min(int(meals_per_day), 6))
        except Exception:
            meals_per_day = 4
        plan = [
            ("08:00", "Breakfast", "a balanced breakfast with a carbohydrate, protein and fruit/vegetable"),
            ("12:00", "Lunch", "a balanced meal with grains/starch, protein and vegetables"),
            ("17:00", "Snack", "a preference-friendly snack such as fruit, yogurt or another suitable option"),
            ("20:00", "Dinner", "a balanced dinner with vegetables, carbohydrate and protein"),
        ]
        if meals_per_day >= 5:
            plan.insert(3, ("15:00", "Snack", "a simple snack that fits your preferences"))
        if meals_per_day >= 6:
            plan.insert(4, ("18:00", "Snack", "another small preference-friendly snack"))
        plan = plan[:meals_per_day]
        self.meals = {t: f"{label} — {desc}" for t, label, desc in plan}
        self._save_meals()
        lines = ["Meal plan generated from your saved profile:", ""]
        lines.extend(f"**{t}**  {meal}" for t, meal in self.meals.items())
        if self.profile.get("allergies"):
            lines += ["", "Allergies to avoid: " + ", ".join(map(str, self.profile["allergies"]))]
        if self.profile.get("preferences"):
            lines += ["Preferences: " + ", ".join(map(str, self.profile["preferences"]))]
        return "\n".join(lines)

    def get_meal_plan(self):
        if not self.meals:
            return "No meal plan has been created yet. Ask me to generate one."
        return "Current meal plan:\n\n" + "\n".join(f"**{t}**  {meal}" for t, meal in self.meals.items())

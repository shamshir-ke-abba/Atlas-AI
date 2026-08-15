"""Atlas Fitness Planner plugin.

The plugin owns the actual profile and planning logic.  The GUI is only one
client of this backend; normal Atlas chat can call the same actions.
"""

import json

from config import DATA_DIR
from plugins.base import AtlasPlugin


class FitnessPlugin(AtlasPlugin):
    name = "fitness"
    display_name = "Fitness Planner"
    description = "Builds profile-aware exercise suggestions and workout plans."
    icon = "🏋️"
    has_gui = True
    gui_id = "fitness"
    priority = 12

    triggers = [
        "fitness", "workout", "exercise", "gym", "training", "reps", "sets",
    ]

    def __init__(self):
        super().__init__()
        self.profile_file = DATA_DIR / "fitness_profile.json"
        self.profile = self._load_profile()

    def _load_profile(self):
        default = {
            "name": None,
            "experience": None,
            "goal": None,
            "equipment": [],
            "restrictions": [],
        }
        if self.profile_file.exists():
            try:
                default.update(json.loads(self.profile_file.read_text(encoding="utf-8")))
            except Exception:
                pass
        return default

    def _save_profile(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.profile_file.write_text(
            json.dumps(self.profile, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def profile_complete(self):
        return bool(self.profile.get("experience") and self.profile.get("goal"))

    def can_handle(self, message):
        text = str(message or "").lower().strip()
        if not text:
            return False
        if any(text == t or text.startswith(t + " ") for t in self.triggers):
            return True
        return any(p in text for p in (
            "how many reps", "how many sets", "how should i train",
            "make me a workout", "generate a workout", "workout plan",
            "my workout", "my gym", "what exercises",
        ))

    def _infer_action(self, message):
        text = str(message or "").lower()
        if any(p in text for p in ("exercise", "exercises", "chest", "back", "shoulder", "legs")):
            return "get_exercises"
        if any(p in text for p in ("workout", "routine", "training plan", "generate a plan", "make a plan")):
            return "generate_workout"
        if any(p in text for p in ("reps", "sets")):
            return "rep_guidance"
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
        if action == "get_exercises":
            return self.get_exercises(kwargs.get("muscle_group") or self._muscle_group(message))
        if action == "generate_workout":
            return self.generate_workout(frequency=kwargs.get("frequency", 3))
        if action == "rep_guidance":
            return self.rep_guidance(message)

        return (
            "I can use your fitness profile to suggest exercises, give general "
            "rep/set guidance, or generate a simple workout plan."
        )

    def set_profile(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.profile and value not in (None, "", []):
                self.profile[key] = value
        self._save_profile()
        return "Fitness profile saved. Atlas can now use it for workout and exercise suggestions."

    def get_profile(self):
        return "Fitness profile:\n" + "\n".join(
            f"• {k.replace('_', ' ').title()}: {v or 'Not set'}"
            for k, v in self.profile.items()
        )

    @staticmethod
    def _muscle_group(message):
        text = str(message or "").lower()
        for group in ("chest", "back", "shoulders", "legs"):
            if group in text:
                return group
        return None

    def get_exercises(self, muscle_group=None):
        exercises = {
            "chest": ["push-ups", "bench press", "incline press"],
            "back": ["rows", "pull-ups", "lat pulldown"],
            "shoulders": ["overhead press", "lateral raises"],
            "legs": ["squats", "lunges", "leg press"],
        }
        if not muscle_group:
            return "Available groups: " + ", ".join(exercises)
        group = str(muscle_group).lower().strip()
        if group not in exercises:
            return f"I don't have an exercise list for '{muscle_group}'."
        return f"{group.title()} exercises:\n" + "\n".join(f"• {x}" for x in exercises[group])

    def rep_guidance(self, message=""):
        return (
            "For general strength/fitness work, repetitions depend on the exercise, "
            "technique and experience rather than simply the weight used. A common "
            "starting range for many resistance exercises is around 8–12 controlled "
            "repetitions, stopping if form breaks down. Atlas can tailor this after "
            "your profile is set."
        )

    def generate_workout(self, frequency=3, **kwargs):
        try:
            frequency = max(1, min(int(frequency), 6))
        except Exception:
            frequency = 3
        goal = self.profile.get("goal") or "general fitness"
        experience = self.profile.get("experience") or "beginner"
        equipment = self.profile.get("equipment") or ["available equipment"]
        if not isinstance(equipment, list):
            equipment = [str(equipment)]
        sessions = [
            "Full-body: squat pattern • push • pull • core",
            "Full-body: hinge pattern • push • pull • core",
            "Full-body: legs • upper body • core",
            "Upper body: push • pull • shoulders",
            "Lower body: squat • hinge • legs",
            "Full-body: lighter technique-focused session",
        ]
        lines = [
            f"{frequency}-day {goal} plan ({experience} level)",
            f"Equipment: {', '.join(map(str, equipment))}",
            "",
        ]
        for i in range(frequency):
            lines.append(f"Day {i + 1}: {sessions[i]}")
        lines += [
            "",
            "Keep technique controlled and adjust difficulty to your experience. "
            "If something hurts, stop and ask a qualified professional."
        ]
        return "\n".join(lines)

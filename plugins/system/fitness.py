"""Atlas Fitness Planner.

Uses the central Atlas ProfileStore as the single source of truth.
The legacy fitness_profile.json is supported as a one-time migration source.
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
        "fitness", "workout", "exercise", "gym", "training",
        "reps", "sets",
    ]

    def __init__(self):
        super().__init__()

        self.profile_file = DATA_DIR / "fitness_profile.json"
        self.profile = self._load_legacy_profile()

        # ToolManager injects the central ProfileStore.
        # This starts as None so the plugin also works safely by itself.
        self.profile_store = None

    # ==========================================================
    # PROFILE STORE
    # ==========================================================

    def set_profile_store(self, profile_store):
        """Receive the central Atlas ProfileStore."""

        self.profile_store = profile_store

        # Migrate useful legacy data if the central profile is empty.
        self._migrate_legacy_profile()

        # Always refresh from the central store afterwards.
        self._refresh_profile()

    def _refresh_profile(self):
        """Refresh the local compatibility view from ProfileStore."""

        if self.profile_store is None:
            return self.profile

        central = self.profile_store.get("fitness", {}) or {}

        identity_name = self.profile_store.get("identity.name")

        self.profile = {
            "name": identity_name,
            "experience": central.get("experience"),
            "goal": central.get("goal"),
            "equipment": central.get("equipment", []),
            "restrictions": central.get("restrictions", []),
        }

        return self.profile

    def _migrate_legacy_profile(self):
        """Move an existing fitness_profile.json into ProfileStore."""

        if self.profile_store is None:
            return

        central = self.profile_store.get("fitness", {}) or {}

        legacy = self.profile

        values = {}

        for key in ("experience", "goal", "equipment", "restrictions"):
            value = legacy.get(key)

            if value not in (None, "", []):
                current = central.get(key)

                if current in (None, "", []):
                    values[key] = value

        if values:
            self.profile_store.update_section(
                "fitness",
                values,
            )

        if not self.profile_store.get("identity.name"):
            if legacy.get("name"):
                self.profile_store.set(
                    "identity.name",
                    legacy["name"],
                )

    # ==========================================================
    # LEGACY COMPATIBILITY
    # ==========================================================

    def _load_legacy_profile(self):
        default = {
            "name": None,
            "experience": None,
            "goal": None,
            "equipment": [],
            "restrictions": [],
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
        """Keep the old file updated for backwards compatibility."""

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

    # ==========================================================
    # PROFILE
    # ==========================================================

    def profile_complete(self):
        self._refresh_profile()

        return bool(
            self.profile.get("experience")
            and self.profile.get("goal")
        )

    def set_profile(self, **kwargs):
        """Save fitness profile into the central ProfileStore."""

        allowed = {
            "name",
            "experience",
            "goal",
            "equipment",
            "restrictions",
        }

        values = {
            key: value
            for key, value in kwargs.items()
            if key in allowed
            and value not in (None, "", [])
        }

        if self.profile_store is not None:

            fitness_values = {
                key: value
                for key, value in values.items()
                if key != "name"
            }

            if fitness_values:
                self.profile_store.update_section(
                    "fitness",
                    fitness_values,
                )

            if "name" in values:
                self.profile_store.set(
                    "identity.name",
                    values["name"],
                )

            self._refresh_profile()

        else:
            self.profile.update(values)
            self._save_legacy_profile()

        return (
            "Fitness profile saved to Atlas memory. "
            "Future fitness requests can use this profile."
        )

    def get_profile(self):
        self._refresh_profile()

        return (
            "Fitness profile:\n"
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
        text = str(message or "").lower().strip()

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
                "how many reps",
                "how many sets",
                "how should i train",
                "make me a workout",
                "generate a workout",
                "workout plan",
                "my workout",
                "my gym",
                "what exercises",
                "fitness profile",
            )
        )

    def _infer_action(self, message):
        text = str(message or "").lower()

        if "profile" in text:
            return "get_profile"

        if any(
            phrase in text
            for phrase in (
                "exercise",
                "exercises",
                "chest",
                "back",
                "shoulder",
                "shoulders",
                "legs",
            )
        ):
            return "get_exercises"

        if any(
            phrase in text
            for phrase in (
                "workout",
                "routine",
                "training plan",
                "generate a plan",
                "make a plan",
            )
        ):
            return "generate_workout"

        if any(
            phrase in text
            for phrase in (
                "reps",
                "sets",
            )
        ):
            return "rep_guidance"

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

        if action == "get_exercises":
            return self.get_exercises(
                kwargs.get("muscle_group")
                or self._muscle_group(message)
            )

        if action == "generate_workout":
            return self.generate_workout(
                frequency=kwargs.get(
                    "frequency",
                    3,
                )
            )

        if action == "rep_guidance":
            return self.rep_guidance(message)

        return (
            "I can use your saved fitness profile to "
            "suggest exercises and build a general workout plan."
        )

    # ==========================================================
    # EXERCISES
    # ==========================================================

    @staticmethod
    def _muscle_group(message):
        text = str(message or "").lower()

        for group in (
            "chest",
            "back",
            "shoulders",
            "legs",
        ):
            if group in text:
                return group

        return None

    def get_exercises(self, muscle_group=None):
        self._refresh_profile()

        exercises = {
            "chest": [
                "push-ups",
                "bench press",
                "incline press",
            ],
            "back": [
                "rows",
                "pull-ups",
                "lat pulldown",
            ],
            "shoulders": [
                "overhead press",
                "lateral raises",
            ],
            "legs": [
                "squats",
                "lunges",
                "leg press",
            ],
        }

        if not muscle_group:
            return (
                "Available groups: "
                + ", ".join(exercises)
            )

        group = str(
            muscle_group
        ).lower().strip()

        if group not in exercises:
            return (
                f"I don't have an exercise list "
                f"for '{muscle_group}'."
            )

        return (
            f"{group.title()} exercises:\n"
            + "\n".join(
                f"• {exercise}"
                for exercise in exercises[group]
            )
        )

    # ==========================================================
    # REP GUIDANCE
    # ==========================================================

    def rep_guidance(self, message=""):
        self._refresh_profile()

        experience = (
            self.profile.get("experience")
            or "beginner"
        )

        return (
            f"Your saved experience level is "
            f"**{experience}**.\n\n"
            "For general resistance training, repetitions "
            "depend on the exercise, technique and experience. "
            "Use controlled movements and choose a difficulty "
            "that lets you maintain good form. Stop if an "
            "exercise causes pain."
        )

    # ==========================================================
    # WORKOUT GENERATION
    # ==========================================================

    def generate_workout(self, frequency=3, **kwargs):
        self._refresh_profile()

        try:
            frequency = max(
                1,
                min(
                    int(frequency),
                    6,
                ),
            )
        except Exception:
            frequency = 3

        goal = (
            self.profile.get("goal")
            or "general fitness"
        )

        experience = (
            self.profile.get("experience")
            or "beginner"
        )

        equipment = (
            self.profile.get("equipment")
            or ["bodyweight / available equipment"]
        )

        restrictions = (
            self.profile.get("restrictions")
            or []
        )

        if not isinstance(
            equipment,
            list,
        ):
            equipment = [str(equipment)]

        if not isinstance(
            restrictions,
            list,
        ):
            restrictions = [str(restrictions)]

        goal_text = str(goal).lower()
        experience_text = str(experience).lower()

        # Personalize session structure.
        if any(
            word in goal_text
            for word in (
                "strength",
                "strong",
            )
        ):
            sessions = [
                "Lower body + controlled strength movements",
                "Upper body push + pull",
                "Lower body + core",
                "Upper body + shoulders",
                "Full body strength-focused session",
                "Technique-focused full body session",
            ]

        elif any(
            word in goal_text
            for word in (
                "endurance",
                "stamina",
                "conditioning",
            )
        ):
            sessions = [
                "Full body + light conditioning",
                "Lower body + steady movement",
                "Upper body + conditioning",
                "Full body circuit-style session",
                "Mobility + conditioning",
                "Light full-body session",
            ]

        else:
            sessions = [
                "Full body: squat pattern • push • pull • core",
                "Full body: hinge pattern • push • pull • core",
                "Full body: legs • upper body • core",
                "Upper body: push • pull • shoulders",
                "Lower body: squat • hinge • legs",
                "Full body: lighter technique-focused session",
            ]

        lines = [
            f"{frequency}-day {goal} plan",
            f"Experience: {experience}",
            f"Equipment: {', '.join(map(str, equipment))}",
        ]

        if restrictions:
            lines.append(
                "Restrictions to keep in mind: "
                + ", ".join(
                    map(str, restrictions)
                )
            )

        lines.append("")

        for index in range(frequency):
            lines.append(
                f"Day {index + 1}: "
                f"{sessions[index]}"
            )

        lines.extend(
            [
                "",
                "Keep movements controlled and "
                "adjust difficulty to your experience. "
                "If something hurts, stop and seek "
                "appropriate professional guidance.",
            ]
        )

        return "\n".join(lines)

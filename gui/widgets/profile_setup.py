"""
Interactive profile forms used by Atlas.

The forms collect useful health/fitness context without asking for
body-weight or appearance measurements.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class ProfileSetupCard(QFrame):
    submitted = Signal(str, dict)

    def __init__(self, tool, controller=None, parent=None):
        super().__init__(parent)
        self.tool = str(tool).lower().strip()
        self.controller = controller
        self.fields = {}
        self.setObjectName("ProfileSetupCard")
        self.build_ui()

    def add_line(self, form, key, label, placeholder=""):
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        self.fields[key] = field
        form.addRow(label, field)

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        title = QLabel(
            "🏋️ Set up your fitness profile"
            if self.tool == "fitness"
            else "🥗 Set up your nutrition profile"
        )
        title.setObjectName("ProfileTitle")
        root.addWidget(title)

        subtitle = QLabel(
            "A few details help Atlas tailor future suggestions."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("ProfileSubtitle")
        root.addWidget(subtitle)

        form = QFormLayout()
        form.setSpacing(8)
        root.addLayout(form)

        self.add_line(form, "name", "Name", "e.g. Saad")

        if self.tool == "fitness":
            self.add_line(
                form, "experience", "Experience",
                "beginner / intermediate / advanced",
            )
            self.add_line(
                form, "goal", "Goal",
                "strength / general fitness / endurance",
            )
            self.add_line(
                form, "equipment", "Equipment",
                "bodyweight, dumbbells, gym...",
            )
            self.add_line(
                form, "restrictions", "Restrictions",
                "injuries or movements to avoid",
            )
        else:
            self.add_line(form, "age", "Age", "e.g. 16")
            self.add_line(
                form, "activity_level", "Activity",
                "low / moderate / high",
            )
            self.add_line(
                form, "diet_pattern", "Diet",
                "balanced / vegetarian / etc.",
            )
            self.add_line(
                form, "allergies", "Allergies",
                "comma-separated",
            )
            self.add_line(
                form, "intolerances", "Intolerances",
                "comma-separated",
            )
            self.add_line(
                form, "preferences", "Preferences",
                "foods you like/dislike",
            )

        row = QHBoxLayout()
        save = QPushButton("Save profile")
        save.clicked.connect(self.save_profile)
        row.addWidget(save)
        row.addStretch()
        root.addLayout(row)

        self.status = QLabel("")
        self.status.setObjectName("ProfileStatus")
        self.status.setWordWrap(True)
        root.addWidget(self.status)

    @staticmethod
    def clean_value(key, value):
        value = str(value or "").strip()
        if not value:
            return None

        if key in (
            "equipment",
            "restrictions",
            "allergies",
            "intolerances",
            "preferences",
        ):
            return [
                item.strip()
                for item in value.split(",")
                if item.strip()
            ]

        if key == "age":
            try:
                return int(value)
            except ValueError:
                return None

        return value

    def save_profile(self):
        profile = {}

        for key, field in self.fields.items():
            value = self.clean_value(key, field.text())
            if value is not None:
                profile[key] = value

        try:
            if self.controller is not None:
                result = self.controller.apply_tool_profile(self.tool, profile)
            else:
                result = "Profile submitted."
                self.submitted.emit(self.tool, profile)

            # Always emit so standalone tool views can react as well.
            self.submitted.emit(self.tool, profile)
            self.status.setText(f"✓ {result}")
            self.status.setStyleSheet("color:#55d66b; font-weight:600;")
        except Exception as exc:
            self.status.setText(f"Could not save profile: {exc}")
            self.status.setStyleSheet("color:#ff5f56;")

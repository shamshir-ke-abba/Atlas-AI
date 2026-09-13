from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
)


class CodingPermissionDialog(QDialog):
    """Ask the user which Coding Agent capabilities to allow."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Coding Agent Permissions")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        title = QLabel("Coding Agent needs permission")
        title.setStyleSheet(
            "font-size: 18px; font-weight: bold;"
        )
        layout.addWidget(title)

        description = QLabel(
            "Choose what the Coding Agent is allowed to do "
            "for this task."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.read_check = QCheckBox(
            "Read repository"
        )
        self.read_check.setChecked(True)
        self.read_check.setEnabled(False)

        self.search_check = QCheckBox(
            "Search repository"
        )
        self.search_check.setChecked(True)
        self.search_check.setEnabled(False)

        self.write_check = QCheckBox(
            "Modify files"
        )

        self.tests_check = QCheckBox(
            "Run tests"
        )

        self.git_check = QCheckBox(
            "Git operations (coming soon)"
        )
        self.git_check.setEnabled(False)

        layout.addWidget(self.read_check)
        layout.addWidget(self.search_check)
        layout.addWidget(self.write_check)
        layout.addWidget(self.tests_check)
        layout.addWidget(self.git_check)

        buttons = QHBoxLayout()

        cancel_button = QPushButton("Cancel")
        allow_button = QPushButton("Allow")

        cancel_button.clicked.connect(
            self.reject
        )
        allow_button.clicked.connect(
            self.accept
        )

        buttons.addStretch()
        buttons.addWidget(cancel_button)
        buttons.addWidget(allow_button)

        layout.addLayout(buttons)

    def permissions(self):
        return {
            "allow_read": True,
            "allow_search": True,
            "allow_list": True,
            "allow_write": self.write_check.isChecked(),
            "allow_tests": self.tests_check.isChecked(),
            "allow_git": self.git_check.isChecked(),
        }

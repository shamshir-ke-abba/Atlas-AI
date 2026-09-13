import sys

from PySide6.QtWidgets import QApplication

from gui.widgets.coding_permission_dialog import (
    CodingPermissionDialog,
)


def get_app():
    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)

    return app


def test_dialog_defaults_are_safe():
    get_app()

    dialog = CodingPermissionDialog()

    permissions = dialog.permissions()

    assert permissions["allow_read"] is True
    assert permissions["allow_search"] is True
    assert permissions["allow_list"] is True
    assert permissions["allow_write"] is False
    assert permissions["allow_tests"] is False
    assert permissions["allow_git"] is False

    dialog.close()


def test_dialog_returns_selected_permissions():
    get_app()

    dialog = CodingPermissionDialog()

    dialog.write_check.setChecked(True)
    dialog.tests_check.setChecked(True)

    permissions = dialog.permissions()

    assert permissions["allow_write"] is True
    assert permissions["allow_tests"] is True
    assert permissions["allow_git"] is False

    dialog.close()


def test_dialog_can_enable_git():
    get_app()

    dialog = CodingPermissionDialog()

    dialog.git_check.setChecked(True)

    permissions = dialog.permissions()

    assert permissions["allow_git"] is True

    dialog.close()

from agents.coding.permission_manager import (
    CodingPermissionManager,
)


def test_permissions_are_safe_by_default():
    manager = CodingPermissionManager()

    permissions = manager.permissions()

    assert permissions.allow_read is True
    assert permissions.allow_search is True
    assert permissions.allow_list is True
    assert permissions.allow_write is False
    assert permissions.allow_tests is False
    assert permissions.allow_git is False


def test_approve_write_and_tests():
    manager = CodingPermissionManager()

    manager.approve(
        allow_write=True,
        allow_tests=True,
    )

    permissions = manager.permissions()

    assert permissions.allow_write is True
    assert permissions.allow_tests is True
    assert permissions.allow_git is False


def test_git_requires_explicit_approval():
    manager = CodingPermissionManager()

    manager.approve(
        allow_write=True,
        allow_tests=True,
        allow_git=True,
    )

    permissions = manager.permissions()

    assert permissions.allow_git is True


def test_reset_removes_permissions():
    manager = CodingPermissionManager()

    manager.approve(
        allow_write=True,
        allow_tests=True,
        allow_git=True,
    )

    manager.reset()

    permissions = manager.permissions()

    assert permissions.allow_write is False
    assert permissions.allow_tests is False
    assert permissions.allow_git is False


def test_permission_status():
    manager = CodingPermissionManager()

    manager.approve(
        allow_write=True,
        allow_tests=True,
    )

    assert manager.status() == {
        "read": True,
        "search": True,
        "list": True,
        "write": True,
        "tests": True,
        "git": False,
    }


def test_permission_requirements():
    manager = CodingPermissionManager()

    assert manager.needs_write_permission() is True
    assert manager.needs_test_permission() is True
    assert manager.needs_git_permission() is True

    manager.approve(
        allow_write=True,
        allow_tests=True,
    )

    assert manager.needs_write_permission() is False
    assert manager.needs_test_permission() is False
    assert manager.needs_git_permission() is True

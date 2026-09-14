"""
Tests for Phase 9 — Native UI Interaction, Layout & Tool Integration.
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QScrollArea, QSizePolicy

from core.bus import EventBus
from core.controller import Controller
from gui.theme import is_reduced_motion, set_reduced_motion
from gui.widgets.chat import AtlasChat
from gui.widgets.inputbar import AtlasInputBar
from gui.widgets.message import AtlasMessage
from gui.widgets.settings_dialog import SettingsDialog
from gui.widgets.sidebar import AtlasSidebar
from gui.widgets.state_indicator import AtlasStateIndicator
from gui.widgets.statusbar import AtlasStatusBar
from gui.widgets.tool_workspace import (
    CodingToolWidget,
    ProfileToolView,
    PromptToolWidget,
    ToolWorkspace,
)
from gui.window import AtlasWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def controller(qapp):
    bus = EventBus()
    ctrl = Controller(bus)
    return ctrl


def test_state_indicator(qapp):
    indicator = AtlasStateIndicator()
    assert indicator.objectName() == "AtlasStateIndicator"

    # Test thinking state
    indicator.set_state("thinking", "Thinking")
    assert indicator.label.text() == "Thinking"
    assert not indicator.track.isHidden()

    # Test tool state
    indicator.set_state("tool", "Using Calendar")
    assert indicator.label.text() == "Using Calendar"
    assert not indicator.track.isHidden()

    # Test searching state
    indicator.set_state("searching", "Searching web")
    assert indicator.label.text() == "Searching web"
    assert not indicator.track.isHidden()

    # Test success state
    indicator.set_state("success", "Done")
    assert indicator.label.text() == "Done"
    assert indicator.track.isHidden()

    # Test error state
    indicator.set_state("error", "An error occurred")
    assert indicator.label.text() == "An error occurred"
    assert indicator.track.isHidden()

    # Test offline state
    indicator.set_state("offline", "Offline")
    assert indicator.label.text() == "Offline"
    assert indicator.track.isHidden()

    indicator.stop()


def test_reduced_motion_preference(qapp):
    initial = is_reduced_motion()
    try:
        set_reduced_motion(True)
        assert is_reduced_motion() is True

        indicator = AtlasStateIndicator()
        indicator.set_state("thinking", "Thinking")
        indicator.track.start_animation()
        # With reduced motion, timer must NOT be running
        assert not indicator.track._timer.isActive()

        set_reduced_motion(False)
        assert is_reduced_motion() is False
        indicator.track.start_animation()
        assert indicator.track._timer.isActive()
        indicator.stop()
    finally:
        set_reduced_motion(initial)


def test_composer_geometry_stability(qapp):
    input_bar = AtlasInputBar()
    assert input_bar.sizePolicy().verticalPolicy() == QSizePolicy.Fixed
    assert input_bar.minimumHeight() == 66
    assert input_bar.maximumHeight() == 66
    assert input_bar.send_button.width() == 76
    assert input_bar.send_button.height() == 40

    # Switch to generating (stop) mode
    input_bar.set_generating(True)
    assert input_bar.send_button.text() == "■"
    assert input_bar.send_button.width() == 76
    assert input_bar.send_button.height() == 40
    assert input_bar.height() == 66

    # Switch back to idle mode
    input_bar.set_generating(False)
    assert input_bar.send_button.text() == "Send"
    assert input_bar.send_button.width() == 76
    assert input_bar.send_button.height() == 40
    assert input_bar.height() == 66


def test_message_state_indicator_integration(qapp):
    msg = AtlasMessage("Atlas", "")
    assert hasattr(msg, "state_indicator")
    assert not msg.state_indicator.isHidden()
    assert msg.message_label.isHidden()

    msg.set_text("Here is the completed response.")
    assert msg.state_indicator.isHidden()
    assert not msg.message_label.isHidden()
    assert "Here is the completed response." in msg.message_label.text()

    msg.set_state("searching", "Searching web...")
    assert not msg.state_indicator.isHidden()
    assert msg.message_label.isHidden()
    assert msg.state_indicator.label.text() == "Searching web..."

    msg.finish_state()


def test_nutrition_planner_scroll_area(controller, qapp):
    view = ProfileToolView("nutrition", controller)
    scroll = view.findChild(QScrollArea, "ToolScroll")
    assert scroll is not None, "ProfileToolView must enclose content inside QScrollArea #ToolScroll"
    assert scroll.widgetResizable() is True
    assert view.result.objectName() == "ToolResultBrowser"


def test_web_search_scroll_area(controller, qapp):
    meta = {
        "name": "web_search",
        "display_name": "Web Search",
        "icon": "🌐",
        "description": "Search the live web for current information, documentation, news, or technical references.",
    }
    view = PromptToolWidget(controller, meta)
    scroll = view.findChild(QScrollArea, "ToolScroll")
    assert scroll is not None, "PromptToolWidget must enclose content inside QScrollArea #ToolScroll"
    assert scroll.widgetResizable() is True
    assert view.result.objectName() == "ToolResultBrowser"


def test_coding_tool_widget_integration(controller, qapp):
    meta = {
        "name": "coding",
        "display_name": "Coding Agent",
        "icon": "💻",
        "description": "Autonomous coding agent for repository inspection, code editing, and test verification.",
        "enabled": True,
    }
    workspace = ToolWorkspace(controller)
    workspace.refresh_tools()

    # Verify Coding Agent is in the tools catalog
    coding_view = workspace.create_view(meta)
    assert isinstance(coding_view, CodingToolWidget)

    scroll = coding_view.findChild(QScrollArea, "ToolScroll")
    assert scroll is not None, "CodingToolWidget must enclose content inside QScrollArea #ToolScroll"

    # Test result formatting on CodingWorkflowResult
    from agents.coding.workflow import CodingWorkflowResult

    mock_result = CodingWorkflowResult(
        success=True,
        task="Add docstrings",
        message="Changes applied successfully.",
        applied_changes=["core/helpers.py"],
        test_result={"summary": "1 test passed", "passed": 1, "failed": 0},
    )
    coding_view._on_coding_result(mock_result)
    assert "✓ Coding Task Completed Successfully" in coding_view.result.toPlainText() or "✓ Coding Task Completed Successfully" in coding_view.result.toHtml()
    assert coding_view.status_label.text() == "✓ Success"


def test_settings_dialog(controller, qapp):
    dialog = SettingsDialog(controller=controller)
    assert dialog.objectName() == "SettingsDialog"
    assert dialog.clear_memory_btn.objectName() == "SettingsDangerButton"
    assert dialog.clear_history_btn.objectName() == "SettingsDangerButton"
    assert dialog.motion_check is not None

    initial_motion = is_reduced_motion()
    try:
        dialog.toggle_reduced_motion(True)
        assert is_reduced_motion() is True
        dialog.toggle_reduced_motion(False)
        assert is_reduced_motion() is False
    finally:
        set_reduced_motion(initial_motion)


def test_sidebar_conversations_hierarchy(controller, qapp):
    sidebar = AtlasSidebar(bus=controller.bus, controller=controller)
    assert sidebar.new_chat_button.objectName() == "NewChatButton"
    separator = sidebar.findChild(QFrame, "HistorySeparator")
    assert separator is not None, "Sidebar must contain HistorySeparator dividing header from conversation list"
    assert sidebar.history_list.objectName() == "HistoryList"
    assert sidebar.tools_button.objectName() == "ToolsButton"


def test_statusbar_hierarchy(controller, qapp):
    statusbar = AtlasStatusBar(
        bus=controller.bus,
        controller=controller,
        state=controller.state,
    )
    assert statusbar.state_card.findChild(QLabel, "StatusCardTitle").text() == "CURRENT STATE"
    assert statusbar.model_card.findChild(QLabel, "StatusCardTitle").text() == "MODEL"
    assert statusbar.activity_card.findChild(QLabel, "StatusCardTitle").text() == "ACTIVITY"
    assert statusbar.chat_card.findChild(QLabel, "StatusCardTitle").text() == "SESSION"
    assert statusbar.runtime_card.findChild(QLabel, "StatusCardTitle").text() == "SYSTEM"
    assert statusbar.settings_button.objectName() == "StatusSettingsButton"


def test_window_geometry_stability_and_views(controller, qapp):
    window = AtlasWindow(controller.bus, controller.state, controller)

    # Test supported sizes from requirements
    for w, h in ((1366, 768), (1024, 768), (1000, 650)):
        window.resize(w, h)
        QApplication.processEvents()
        assert window.width() >= 1000
        assert window.height() >= 650
        assert window.sidebar.width() == 260
        assert window.status.width() == 280
        assert window.content_stack.width() > 400

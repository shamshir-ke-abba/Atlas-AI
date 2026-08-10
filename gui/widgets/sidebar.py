"""
gui/widgets/sidebar.py

Atlas Sidebar Widget.
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QInputDialog,
    QMessageBox,
)


class AtlasSidebar(QWidget):

    conversation_loaded = Signal(object)

    def __init__(
        self,
        bus,
        controller=None,
        parent=None,
    ):

        super().__init__(parent)

        self.bus = bus
        self.controller = controller

        self.setObjectName(
            "Sidebar"
        )

        self.build_ui()

        self.refresh_history()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        layout.setSpacing(
            10
        )

        # ---------------------------------
        # Atlas Logo
        # ---------------------------------

        self.logo = QLabel()

        self.logo.setObjectName(
            "AtlasLogo"
        )

        self.logo.setAlignment(
            Qt.AlignCenter
        )

        logo_path = (
            Path(__file__).resolve().parent.parent.parent
            / "assets"
            / "Atlas.png"
        )

        if logo_path.exists():

            pixmap = QPixmap(
                str(logo_path)
            )

            if not pixmap.isNull():

                self.logo.setPixmap(
                    pixmap.scaled(
                        180,
                        80,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )

        else:

            # Fallback if the logo cannot be found.
            self.logo.setText(
                "Atlas AI"
            )

        layout.addWidget(
            self.logo
        )

        # ---------------------------------
        # New Chat
        # ---------------------------------

        self.new_chat_button = QPushButton(
            "+ New Chat"
        )

        self.new_chat_button.clicked.connect(
            self.handle_new_chat
        )

        layout.addWidget(
            self.new_chat_button
        )

        # ---------------------------------
        # History
        # ---------------------------------

        history_label = QLabel(
            "CHAT HISTORY"
        )

        history_label.setObjectName(
            "HistoryTitle"
        )

        layout.addWidget(
            history_label
        )

        self.history_list = QListWidget()

        self.history_list.setObjectName(
            "HistoryList"
        )

        self.history_list.itemClicked.connect(
            self.handle_history_clicked
        )

        self.history_list.setContextMenuPolicy(
            Qt.CustomContextMenu
        )

        self.history_list.customContextMenuRequested.connect(
            self.show_history_menu
        )

        layout.addWidget(
            self.history_list,
            1,
        )

        layout.addStretch()

    # =====================================================
    # History
    # =====================================================

    def refresh_history(self):

        self.history_list.clear()

        if self.controller is None:
            return

        conversations = (
            self.controller.list_conversations()
        )

        active_id = (
            self.controller.state.active_conversation_id
        )

        for conversation in conversations:

            item = QListWidgetItem(
                conversation.get(
                    "title",
                    "New Conversation",
                )
            )

            item.setData(
                Qt.UserRole,
                conversation.get("id"),
            )

            self.history_list.addItem(
                item
            )

            if conversation.get("id") == active_id:

                self.history_list.setCurrentItem(
                    item
                )

    # =====================================================
    # New Chat
    # =====================================================

    def handle_new_chat(self):

        if self.controller is None:
            return

        conversation_id = (
            self.controller.new_conversation()
        )

        # Tell the chat widget to clear itself.
        self.conversation_loaded.emit(
            self.controller.get_active_conversation()
        )

        self.refresh_history()

    # =====================================================
    # Load Conversation
    # =====================================================

    def handle_history_clicked(
        self,
        item,
    ):

        conversation_id = item.data(
            Qt.UserRole
        )

        if not conversation_id:
            return

        if self.controller is None:
            return

        success = (
            self.controller.load_conversation(
                conversation_id
            )
        )

        if not success:
            return

        conversation = (
            self.controller.get_active_conversation()
        )

        self.conversation_loaded.emit(
            conversation
        )

        self.refresh_history()

    # =====================================================
    # Context Menu
    # =====================================================

    def show_history_menu(
        self,
        position,
    ):

        item = self.history_list.itemAt(
            position
        )

        if item is None:
            return

        conversation_id = item.data(
            Qt.UserRole
        )

        if not conversation_id:
            return

        menu = QMenu(
            self
        )

        rename_action = menu.addAction(
            "Rename"
        )

        delete_action = menu.addAction(
            "Delete"
        )

        action = menu.exec(
            self.history_list.mapToGlobal(
                position
            )
        )

        if action == rename_action:

            self.rename_conversation(
                conversation_id,
                item,
            )

        elif action == delete_action:

            self.delete_conversation(
                conversation_id
            )

    # =====================================================
    # Rename
    # =====================================================

    def rename_conversation(
        self,
        conversation_id,
        item,
    ):

        current_title = item.text()

        title, accepted = QInputDialog.getText(
            self,
            "Rename Conversation",
            "Conversation name:",
            text=current_title,
        )

        if not accepted:
            return

        title = title.strip()

        if not title:
            return

        success = (
            self.controller.rename_conversation(
                conversation_id,
                title,
            )
        )

        if success:

            self.refresh_history()

    # =====================================================
    # Delete
    # =====================================================

    def delete_conversation(
        self,
        conversation_id,
    ):

        reply = QMessageBox.question(
            self,
            "Delete Conversation",
            "Are you sure you want to delete this conversation?",
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        success = (
            self.controller.delete_conversation(
                conversation_id
            )
        )

        if success:

            self.refresh_history()
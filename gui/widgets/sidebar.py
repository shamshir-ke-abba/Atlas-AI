"""
Atlas V3 Sidebar.
Tools is permanently below conversation history.
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap
from core.events import MessageReceived

from PySide6.QtWidgets import (
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class AtlasSidebar(QWidget):
    conversation_loaded = Signal(object)
    tools_requested = Signal()

    def __init__(self, bus=None, controller=None, parent=None):
        super().__init__(parent)
        self.bus = bus
        self.controller = controller
        self.setObjectName("Sidebar")
        if self.bus is not None:
            self.bus.subscribe(MessageReceived, self._message_received)
        self.build_ui()
        self.refresh_history()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(10)

        self.logo = QLabel()
        self.logo.setObjectName("AtlasLogo")
        self.logo.setAlignment(Qt.AlignCenter)

        logo_path = Path(__file__).resolve().parents[2] / "assets" / "Atlas.png"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                self.logo.setPixmap(
                    pixmap.scaled(
                        180, 80,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
        if self.logo.pixmap() is None:
            self.logo.setText("Atlas AI")
        layout.addWidget(self.logo)

        self.new_chat_button = QPushButton("+ New Chat")
        self.new_chat_button.clicked.connect(self.handle_new_chat)
        layout.addWidget(self.new_chat_button)

        title = QLabel("CHAT HISTORY")
        title.setObjectName("HistoryTitle")
        layout.addWidget(title)

        self.history_list = QListWidget()
        self.history_list.setObjectName("HistoryList")
        self.history_list.itemClicked.connect(self.handle_history_clicked)
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self.show_history_menu)
        layout.addWidget(self.history_list, 1)

        layout.addSpacing(8)

        self.tools_button = QPushButton("🧰  Tools")
        self.tools_button.setObjectName("ToolsButton")
        self.tools_button.setMinimumHeight(42)
        self.tools_button.clicked.connect(self.tools_requested.emit)
        layout.addWidget(self.tools_button)

    def _message_received(self, event):
        # Controller auto-titles the conversation before the event bus
        # reaches this subscriber, so refresh immediately.
        QTimer.singleShot(0, self.refresh_history)

    def refresh_history(self):
        self.history_list.clear()
        if self.controller is None:
            return

        try:
            conversations = self.controller.get_conversations()
            active_id = self.controller.get_active_conversation_id()
        except Exception:
            return

        if isinstance(conversations, list):
            items = conversations
        elif isinstance(conversations, dict):
            items = []
            for cid, data in conversations.items():
                data = dict(data or {})
                data["id"] = data.get("id", cid)
                items.append(data)
        else:
            items = []

        active_item = None

        for data in items:
            if not isinstance(data, dict) or not data.get("id"):
                continue

            item = QListWidgetItem(
                str(data.get("title") or "New Chat")
            )
            item.setData(Qt.UserRole, str(data["id"]))
            self.history_list.addItem(item)

            if active_id is not None and str(active_id) == str(data["id"]):
                active_item = item

        if active_item is not None:
            self.history_list.setCurrentItem(active_item)

    def handle_new_chat(self):
        if self.controller is None:
            return

        try:
            self.controller.create_conversation()
            conversation = self.controller.get_active_conversation()
            self.refresh_history()
            self.conversation_loaded.emit(conversation)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Atlas",
                f"Could not create new chat:\n\n{exc}",
            )

    def handle_history_clicked(self, item):
        cid = item.data(Qt.UserRole)
        if not cid or self.controller is None:
            return

        try:
            if not self.controller.load_conversation(cid):
                QMessageBox.warning(
                    self,
                    "Atlas",
                    "Could not load conversation.",
                )
                return

            conversation = self.controller.get_active_conversation()
            self.conversation_loaded.emit(conversation)
            self.refresh_history()

        except Exception as exc:
            QMessageBox.warning(
                self,
                "Atlas",
                f"Could not load conversation:\n\n{exc}",
            )

    def show_history_menu(self, position):
        item = self.history_list.itemAt(position)
        if item is None:
            return

        cid = item.data(Qt.UserRole)
        menu = QMenu(self)
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        action = menu.exec(
            self.history_list.mapToGlobal(position)
        )

        if action == rename_action:
            self.rename_conversation(cid)
        elif action == delete_action:
            self.delete_conversation(cid)

    def rename_conversation(self, cid):
        current = self.history_list.currentItem()
        current_title = current.text() if current else "New Chat"

        title, ok = QInputDialog.getText(
            self,
            "Rename Conversation",
            "Conversation name:",
            text=current_title,
        )
        if not ok or not title.strip():
            return

        if self.controller.rename_conversation(cid, title.strip()):
            self.refresh_history()

    def delete_conversation(self, cid):
        if self.controller is None:
            return

        if self.controller.state.is_generating:
            QMessageBox.information(
                self,
                "Atlas",
                "Please wait for Atlas to finish before deleting a chat.",
            )
            return

        if (
            QMessageBox.question(
                self,
                "Delete Conversation",
                "Delete this conversation?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return

        if not self.controller.delete_conversation(cid):
            QMessageBox.warning(
                self,
                "Atlas",
                "Could not delete conversation.",
            )
            return

        conversation = self.controller.get_active_conversation()
        self.refresh_history()
        self.conversation_loaded.emit(conversation)

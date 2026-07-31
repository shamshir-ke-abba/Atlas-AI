"""
Atlas V3 Chat Panel
"""

import tkinter as tk
from tkinter import scrolledtext

from core.events import MessageReceived
from gui import theme


class ChatPanel(tk.Frame):

    def __init__(self, parent, bus):

        super().__init__(
            parent,
            bg=theme.BACKGROUND,
        )

        self.bus = bus

        self.create_widgets()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_widgets(self):

        self.chat = scrolledtext.ScrolledText(

            self,

            wrap=tk.WORD,

            bg=theme.PANEL,

            fg=theme.TEXT,

            insertbackground=theme.TEXT,

            relief=tk.FLAT,

            font=theme.FONT,

            state="disabled",
        )

        self.chat.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=10,
        )

        self.chat.tag_config(
            "sender",
            foreground=theme.ACCENT,
            font=("Segoe UI", 11, "bold"),
        )

        self.chat.tag_config(
            "message",
            foreground=theme.TEXT,
        )

        # ------------------------------

        bottom = tk.Frame(
            self,
            bg=theme.BACKGROUND,
        )

        bottom.pack(
            fill=tk.X,
            padx=10,
            pady=10,
        )

        self.entry = tk.Entry(

            bottom,

            bg=theme.PANEL,

            fg=theme.TEXT,

            insertbackground=theme.TEXT,

            relief=tk.FLAT,

            font=theme.FONT,
        )

        self.entry.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            ipady=8,
        )

        self.entry.bind(
            "<Return>",
            lambda e: self.send_message(),
        )

        self.send_button = tk.Button(

            bottom,

            text="Send",

            command=self.send_message,

            bg=theme.BUTTON,

            fg=theme.TEXT,

            relief=tk.FLAT,

            width=10,
        )

        self.send_button.pack(
            side=tk.RIGHT,
            padx=(8, 0),
        )

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def add_message(
        self,
        sender,
        message,
    ):

        self.chat.config(state="normal")

        self.chat.insert(
            tk.END,
            sender + "\n",
            "sender",
        )

        self.chat.insert(
            tk.END,
            message + "\n\n",
            "message",
        )

        self.chat.config(state="disabled")

        self.chat.yview(tk.END)

    # --------------------------------------------------
    # Send
    # --------------------------------------------------

    def send_message(self):

        text = self.entry.get().strip()

        if not text:
            return

        self.add_message(
            "You",
            text,
        )

        self.entry.delete(
            0,
            tk.END,
        )

        self.bus.publish(
            MessageReceived(text)
        )
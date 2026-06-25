"""Sidebar navigation button component."""

import customtkinter as ctk


class SidebarButton(ctk.CTkButton):
    """Consistent sidebar button for safe placeholder navigation."""

    def __init__(self, master, text: str, command):
        super().__init__(
            master,
            text=text,
            command=command,
            height=38,
            corner_radius=6,
            anchor="w",
        )

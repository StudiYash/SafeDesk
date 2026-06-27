"""Simple read-only information banner."""

import customtkinter as ctk


class InfoBanner(ctk.CTkFrame):
    """Compact banner for setup guidance and status messages."""

    def __init__(self, master, message: str, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.label = ctk.CTkLabel(self, text=message, justify="left", wraplength=760)
        self.label.grid(row=0, column=0, padx=14, pady=10, sticky="ew")

    def set_message(self, message: str) -> None:
        self.label.configure(text=message)

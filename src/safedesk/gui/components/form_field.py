"""Simple labelled form field component."""

import customtkinter as ctk

from safedesk.gui import design_system as ds


class FormField(ctk.CTkFrame):
    """Small labelled text entry wrapper."""

    def __init__(self, master, label: str, placeholder: str = "", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self,
            text=label,
            anchor="w",
            text_color=ds.TEXT_SECONDARY,
            font=ctk.CTkFont(size=ds.FONT_SMALL, weight="bold"),
        ).grid(row=0, column=0, sticky="ew")
        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            fg_color=ds.CARD_BG_ALT,
            border_color=ds.BORDER_MUTED,
            text_color=ds.TEXT_PRIMARY,
            placeholder_text_color=ds.TEXT_MUTED,
        )
        self.entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))

    def get(self) -> str:
        return self.entry.get()

    def set(self, value: str) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

"""Simple labelled form field component."""

import customtkinter as ctk


class FormField(ctk.CTkFrame):
    """Small labelled text entry wrapper."""

    def __init__(self, master, label: str, placeholder: str = "", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=label, anchor="w").grid(row=0, column=0, sticky="ew")
        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder)
        self.entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))

    def get(self) -> str:
        return self.entry.get()

    def set(self, value: str) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

"""Reusable status card component."""

from __future__ import annotations

import customtkinter as ctk


class StatusCard(ctk.CTkFrame):
    """Simple read-only status card for placeholder screens."""

    def __init__(self, master, title: str, rows: list[tuple[str, str]], **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0,
            column=0,
            padx=18,
            pady=(16, 8),
            sticky="w",
        )

        for index, (label, value) in enumerate(rows, start=1):
            ctk.CTkLabel(self, text=f"{label}: {value}", anchor="w", justify="left").grid(
                row=index,
                column=0,
                padx=18,
                pady=3,
                sticky="ew",
            )

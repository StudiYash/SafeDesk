"""Reusable page header component."""

from __future__ import annotations

import customtkinter as ctk

from safedesk.gui import design_system as ds


class PageHeader(ctk.CTkFrame):
    """Compact title and subtitle block for SafeDesk screens."""

    def __init__(self, master, title: str, subtitle: str = "", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=ds.FONT_H1, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        if subtitle:
            ctk.CTkLabel(
                self,
                text=subtitle,
                font=ctk.CTkFont(size=ds.FONT_BODY),
                text_color=ds.TEXT_SECONDARY,
                justify="left",
                anchor="w",
                wraplength=780,
            ).grid(row=1, column=0, sticky="ew", pady=(ds.SPACE_XS, 0))

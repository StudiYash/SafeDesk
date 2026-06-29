"""Reusable SafeDesk status card component."""

from __future__ import annotations

import customtkinter as ctk

from safedesk.gui import design_system as ds


class StatusCard(ctk.CTkFrame):
    """Read-only branded status card."""

    def __init__(self, master, title: str, rows: list[tuple[str, str]], accent: str | None = None, **kwargs):
        style = ds.card_kwargs()
        style.update(kwargs)
        super().__init__(master, **style)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        accent_color = accent or ds.SAFEDESK_RED
        ctk.CTkFrame(self, height=3, fg_color=accent_color, corner_radius=ds.RADIUS_SM).grid(
            row=0,
            column=0,
            columnspan=2,
            padx=ds.SPACE_LG,
            pady=(ds.SPACE_LG, ds.SPACE_SM),
            sticky="ew",
        )

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            padx=ds.SPACE_LG,
            pady=(0, ds.SPACE_SM),
            sticky="w",
        )

        for index, (label, value) in enumerate(rows, start=2):
            ctk.CTkLabel(
                self,
                text=str(label),
                anchor="w",
                justify="left",
                text_color=ds.TEXT_MUTED,
                font=ctk.CTkFont(size=ds.FONT_SMALL),
            ).grid(
                row=index,
                column=0,
                padx=(ds.SPACE_LG, ds.SPACE_SM),
                pady=3,
                sticky="ew",
            )
            ctk.CTkLabel(
                self,
                text=str(value),
                anchor="w",
                justify="left",
                text_color=ds.TEXT_PRIMARY,
                font=ctk.CTkFont(size=ds.FONT_BODY),
                wraplength=360,
            ).grid(
                row=index,
                column=1,
                padx=(ds.SPACE_SM, ds.SPACE_LG),
                pady=3,
                sticky="ew",
            )

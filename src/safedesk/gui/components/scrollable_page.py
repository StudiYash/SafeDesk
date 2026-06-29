"""Reusable full-width scrollable page surface."""

from __future__ import annotations

import customtkinter as ctk

from safedesk.gui import design_system as ds


class ScrollablePage(ctk.CTkScrollableFrame):
    """Scrollable content area for pages that can exceed the window height."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=ds.CONTENT_BG,
            scrollbar_button_color=ds.BORDER_MUTED,
            scrollbar_button_hover_color=ds.SAFEDESK_RED,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

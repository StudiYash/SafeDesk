"""Sidebar navigation button component."""

import customtkinter as ctk

from safedesk.gui import design_system as ds


class SidebarButton(ctk.CTkButton):
    """Consistent SafeDesk sidebar button."""

    def __init__(self, master, text: str, command):
        super().__init__(
            master,
            text=text,
            command=command,
            height=40,
            corner_radius=ds.RADIUS_SM,
            anchor="w",
            fg_color="transparent",
            hover_color=ds.CARD_BG_ALT,
            text_color=ds.TEXT_SECONDARY,
            border_width=1,
            border_color=ds.SIDEBAR_BG,
        )
        self._active = False

    def set_active(self, active: bool) -> None:
        self._active = active
        if active:
            self.configure(
                fg_color=ds.SAFEDESK_RED,
                hover_color=ds.SAFEDESK_DEEP_RED,
                text_color=ds.TEXT_PRIMARY,
                border_color=ds.SAFEDESK_RED,
            )
        else:
            self.configure(
                fg_color="transparent",
                hover_color=ds.CARD_BG_ALT,
                text_color=ds.TEXT_SECONDARY,
                border_color=ds.SIDEBAR_BG,
            )

"""Dashboard placeholder screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.status_card import StatusCard


class DashboardPlaceholderScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.grid_columnconfigure(0, weight=1)

        PageHeader(
            self,
            "Dashboard",
            "Future evidence, event history, and review surfaces will live here.",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 12))

        InfoBanner(
            self,
            "No database is accessed and no real records exist in this phase.",
            kind="neutral",
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 12))

        StatusCard(
            self,
            "Dashboard Scope",
            [
                ("Intruder history", "future placeholder"),
                ("SQLite logs", "not implemented"),
                ("Evidence review", "not active"),
                ("Data source", "none in this phase"),
            ],
            accent=ds.SAFEDESK_NEUTRAL,
        ).grid(row=2, column=0, sticky="ew", padx=4, pady=6)

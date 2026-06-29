"""Protected mode preview placeholder screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.status_card import StatusCard


class ProtectedModePreviewScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.grid_columnconfigure(0, weight=1)

        PageHeader(
            self,
            "Protected Mode Preview",
            "A non-operational preview of the future protected SafeDesk experience.",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 12))

        InfoBanner(
            self,
            "This is a preview only. No real protected mode is active. "
            "No lockdown, fullscreen enforcement, camera access, or shutdown behavior is enabled.",
            kind="danger",
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 12))

        StatusCard(
            self,
            "Preview Boundary",
            [
                ("Fullscreen lock", "not active"),
                ("Input lockdown", "not implemented"),
                ("Shutdown escalation", "not implemented"),
                ("Camera access", "not started from this page"),
                ("Future phase", "Phase 14"),
            ],
            accent=ds.SAFEDESK_DEEP_RED,
        ).grid(row=2, column=0, sticky="ew", padx=4, pady=6)

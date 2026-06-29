"""Settings placeholder screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.status_card import StatusCard


class SettingsPlaceholderScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.grid_columnconfigure(0, weight=1)

        PageHeader(
            self,
            "Settings",
            "Future local preferences will be managed here with strict safety controls.",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 12))

        InfoBanner(
            self,
            "Real-risk controls cannot be toggled from this placeholder shell.",
            kind="warning",
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 12))

        StatusCard(
            self,
            "Safe Feature Flags",
            [
                ("Real email", "enabled" if context.settings.real_email_enabled else "disabled"),
                ("Real shutdown", "enabled" if context.settings.real_shutdown_enabled else "disabled"),
                ("Real lockdown", "enabled" if context.settings.real_lockdown_enabled else "disabled"),
                ("Demo/safe mode", "enabled" if context.settings.demo_safe_mode else "disabled"),
            ],
            accent=ds.SAFEDESK_ALERT,
        ).grid(row=2, column=0, sticky="ew", padx=4, pady=6)

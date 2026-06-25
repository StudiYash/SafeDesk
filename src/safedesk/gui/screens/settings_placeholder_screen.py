"""Settings placeholder screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui.components.status_card import StatusCard


class SettingsPlaceholderScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0,
            column=0,
            sticky="w",
            padx=6,
            pady=(0, 12),
        )
        ctk.CTkLabel(
            self,
            text="Future settings will appear here. Real-risk controls cannot be toggled from this placeholder shell.",
            wraplength=780,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=6, pady=(0, 12))

        StatusCard(
            self,
            "Safe Feature Flags",
            [
                ("Real email", "enabled" if context.settings.real_email_enabled else "disabled"),
                ("Real shutdown", "enabled" if context.settings.real_shutdown_enabled else "disabled"),
                ("Real lockdown", "enabled" if context.settings.real_lockdown_enabled else "disabled"),
                ("Demo/safe mode", "enabled" if context.settings.demo_safe_mode else "disabled"),
            ],
        ).grid(row=2, column=0, sticky="ew", padx=6, pady=6)

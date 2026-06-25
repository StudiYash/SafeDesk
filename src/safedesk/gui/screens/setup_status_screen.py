"""Setup status placeholder screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui.components.status_card import StatusCard


class SetupStatusScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Setup Status", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0,
            column=0,
            sticky="w",
            padx=6,
            pady=(0, 12),
        )

        StatusCard(
            self,
            "Configuration Readiness",
            [
                ("Configuration loaded", "yes"),
                ("Local config loaded", "yes" if context.load_result.local_config_loaded else "no"),
                (".env loaded", "yes" if context.env.env_file_loaded else "no"),
                ("Safe mode", "enabled" if context.settings.demo_safe_mode else "disabled"),
                ("Future setup wizard", "placeholder only"),
            ],
        ).grid(row=1, column=0, sticky="ew", padx=6, pady=6)

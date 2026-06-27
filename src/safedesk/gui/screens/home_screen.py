"""Home placeholder screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.config.setup_state import get_setup_status
from safedesk.gui.components.status_card import StatusCard


class HomeScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master)
        setup_status = get_setup_status(context.load_result.config, context.load_result, context.env)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Welcome to SafeDesk", font=ctk.CTkFont(size=26, weight="bold")).grid(
            row=0,
            column=0,
            sticky="w",
            padx=6,
            pady=(0, 12),
        )
        ctk.CTkLabel(
            self,
            text="This is the SafeDesk GUI shell foundation. Application features will be added phase by phase.",
            wraplength=760,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=6, pady=(0, 18))

        StatusCard(
            self,
            "Current Runtime",
            [
                ("Environment", context.settings.environment),
                ("Security mode", context.settings.security_mode),
                ("Demo/safe mode", "enabled" if context.settings.demo_safe_mode else "disabled"),
                ("Setup", "complete" if setup_status.setup_completed else "incomplete"),
                ("Local config", "loaded" if setup_status.local_config_loaded else "not loaded"),
                ("Configuration", "valid" if context.report.is_valid else "review required"),
            ],
        ).grid(row=2, column=0, sticky="ew", padx=6, pady=6)

"""Setup status placeholder screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.config.setup_state import get_setup_status
from safedesk.gui.components.status_card import StatusCard


class SetupStatusScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master)
        setup_status = get_setup_status(context.load_result.config, context.load_result, context.env)
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
                ("Setup completed", "yes" if setup_status.setup_completed else "no"),
                ("Local config loaded", "yes" if setup_status.local_config_loaded else "no"),
                (".env loaded", "yes" if setup_status.env_loaded else "no"),
                ("Owner name configured", "yes" if setup_status.owner_name_configured else "no"),
                ("Owner email configured", "yes" if setup_status.owner_email_configured else "no"),
                ("Demo/safe mode", "enabled" if setup_status.demo_safe_mode_enabled else "disabled"),
                ("Future face registration", setup_status.face_registration_status),
                ("Future password setup", setup_status.password_setup_status),
                ("Future OTP setup", setup_status.otp_setup_status),
            ],
        ).grid(row=1, column=0, sticky="ew", padx=6, pady=6)

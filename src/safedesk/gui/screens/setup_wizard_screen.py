"""Safe first-time setup wizard screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.config.local_config_writer import LocalSetupPayload, save_local_setup_config
from safedesk.config.exceptions import SafeDeskConfigError
from safedesk.gui.components.form_field import FormField
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.utils.constants import SUPPORTED_SECURITY_MODES


class SetupWizardScreen(ctk.CTkFrame):
    """Collect safe, non-secret local setup values."""

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master)
        self.context = context
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="First-Time Setup Wizard", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0,
            column=0,
            sticky="w",
            padx=6,
            pady=(0, 10),
        )
        InfoBanner(
            self,
            "This setup saves only non-secret local preferences. No password is created, no face image is captured, "
            "no email or OTP is configured, and no lockdown or shutdown is enabled in this phase.",
        ).grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 12))

        self.owner_name = FormField(self, "Owner display name", "Example: Yash")
        self.owner_name.grid(row=2, column=0, sticky="ew", padx=6, pady=6)
        self.owner_name.set(context.load_result.config.get("owner_profile", {}).get("owner_name", ""))

        self.owner_email = FormField(self, "Owner email address (optional)", "owner@example.com")
        self.owner_email.grid(row=3, column=0, sticky="ew", padx=6, pady=6)
        self.owner_email.set(context.load_result.config.get("owner_profile", {}).get("owner_email", ""))

        ctk.CTkLabel(self, text="Preferred security mode", anchor="w").grid(row=4, column=0, sticky="ew", padx=6, pady=(8, 0))
        self.security_mode = ctk.CTkOptionMenu(self, values=list(SUPPORTED_SECURITY_MODES))
        self.security_mode.set(context.settings.security_mode if context.settings.security_mode in SUPPORTED_SECURITY_MODES else "demo_safe")
        self.security_mode.grid(row=5, column=0, sticky="w", padx=6, pady=(4, 6))

        self.camera_index = FormField(self, "Camera index placeholder", "0")
        self.camera_index.grid(row=6, column=0, sticky="ew", padx=6, pady=6)
        self.camera_index.set("0")

        self.privacy_ack = ctk.BooleanVar(value=False)
        self.safe_mode_ack = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self,
            text="I understand owner/intruder images, logs, and secrets must stay local and out of Git.",
            variable=self.privacy_ack,
        ).grid(row=7, column=0, sticky="w", padx=6, pady=(10, 4))
        ctk.CTkCheckBox(
            self,
            text="I understand real email, lockdown, and shutdown remain disabled in this setup phase.",
            variable=self.safe_mode_ack,
        ).grid(row=8, column=0, sticky="w", padx=6, pady=4)

        self.status_banner = InfoBanner(self, "Ready to save safe local setup preferences.")
        self.status_banner.grid(row=9, column=0, sticky="ew", padx=6, pady=(12, 8))

        ctk.CTkButton(self, text="Save Local Setup", command=self._save_setup).grid(row=10, column=0, sticky="w", padx=6, pady=8)

    def _save_setup(self) -> None:
        try:
            camera_index = int(self.camera_index.get().strip())
            payload = LocalSetupPayload(
                owner_name=self.owner_name.get(),
                owner_email=self.owner_email.get(),
                preferred_security_mode=self.security_mode.get(),
                demo_safe_mode=True,
                camera_index=camera_index,
                privacy_acknowledged=bool(self.privacy_ack.get()),
                safe_mode_acknowledged=bool(self.safe_mode_ack.get()),
            )
            save_local_setup_config(payload)
        except ValueError:
            self.status_banner.set_message("Camera index must be a whole number such as 0.")
            return
        except SafeDeskConfigError as exc:
            self.status_banner.set_message(f"Setup could not be saved: {exc}")
            return

        self.status_banner.set_message(
            "Local setup saved to config.local.json. Restart or re-open SafeDesk to reload local configuration."
        )

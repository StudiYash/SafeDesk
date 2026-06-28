"""Setup status placeholder screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.config.setup_state import get_setup_status
from safedesk.gui.components.status_card import StatusCard
from safedesk.storage.paths import project_root
from safedesk.vision.owner_manifest import build_registration_status


class SetupStatusScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master)
        setup_status = get_setup_status(context.load_result.config, context.load_result, context.env)
        owner_registration = context.load_result.config.get("owner_face_registration", {})
        samples_dir = project_root() / owner_registration.get("samples_dir", "data/owner/samples")
        manifest_path = project_root() / owner_registration.get("manifest_path", "data/config/owner_registration_manifest.json")
        required_samples = int(owner_registration.get("required_samples", 5))
        registration_status = build_registration_status(samples_dir, manifest_path, required_samples)
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
                (
                    "Owner face registration",
                    "completed" if registration_status.registration_complete else "pending",
                ),
                ("Owner face samples", f"{registration_status.sample_count} saved / {registration_status.required_sample_count} required"),
                ("Future password setup", setup_status.password_setup_status),
                ("Future OTP setup", setup_status.otp_setup_status),
            ],
        ).grid(row=1, column=0, sticky="ew", padx=6, pady=6)

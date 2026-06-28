"""Home placeholder screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.config.setup_state import get_setup_status
from safedesk.gui.components.status_card import StatusCard
from safedesk.storage.paths import project_root
from safedesk.vision.owner_manifest import build_registration_status


class HomeScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master)
        setup_status = get_setup_status(context.load_result.config, context.load_result, context.env)
        owner_registration = context.load_result.config.get("owner_face_registration", {})
        samples_dir = project_root() / owner_registration.get("samples_dir", "data/owner/samples")
        manifest_path = project_root() / owner_registration.get("manifest_path", "data/config/owner_registration_manifest.json")
        registration_status = build_registration_status(
            samples_dir,
            manifest_path,
            int(owner_registration.get("required_samples", 5)),
        )
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
                (
                    "Owner face registration",
                    "completed" if registration_status.registration_complete else "pending",
                ),
                ("Owner samples", f"{registration_status.sample_count} saved / {registration_status.required_sample_count} required"),
                ("Configuration", "valid" if context.report.is_valid else "review required"),
            ],
        ).grid(row=2, column=0, sticky="ew", padx=6, pady=6)

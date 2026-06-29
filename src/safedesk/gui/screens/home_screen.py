"""Home placeholder screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.config.setup_state import get_setup_status
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.gui.components.status_card import StatusCard
from safedesk.storage.paths import project_root
from safedesk.vision.owner_manifest import build_registration_status


class HomeScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        setup_status = get_setup_status(context.load_result.config, context.load_result, context.env)
        owner_registration = context.load_result.config.get("owner_face_registration", {})
        samples_dir = project_root() / owner_registration.get("samples_dir", "data/owner/samples")
        manifest_path = project_root() / owner_registration.get("manifest_path", "data/config/owner_registration_manifest.json")
        registration_status = build_registration_status(
            samples_dir,
            manifest_path,
            int(owner_registration.get("required_samples", 5)),
        )
        recognition_config = context.load_result.config.get("owner_recognition", {})
        recognition_required = int(recognition_config.get("minimum_samples_required", 5))
        recognition_ready = registration_status.sample_count >= recognition_required
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self)
        page.grid(row=0, column=0, sticky="nsew")
        for column in (0, 1):
            page.grid_columnconfigure(column, weight=1, uniform="home")

        PageHeader(
            page,
            "SafeDesk Control Overview",
            "A local-first security shell for owner-controlled laptop protection. Current screens remain demo-safe while the project grows phase by phase.",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 12))

        InfoBanner(
            page,
            "SafeDesk is active in foundation/demo scope. No protected mode, lockdown, shutdown, intruder capture, or final unlock behavior runs from this dashboard.",
            kind="info",
            compact=True,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 12))

        StatusCard(
            page,
            "Runtime State",
            [
                ("Environment", context.settings.environment),
                ("Security mode", context.settings.security_mode),
                ("Demo/safe mode", "enabled" if context.settings.demo_safe_mode else "disabled"),
                ("Configuration", "valid" if context.report.is_valid else "review required"),
            ],
            accent=ds.SAFEDESK_RED,
        ).grid(row=2, column=0, sticky="nsew", padx=(4, 8), pady=6)

        StatusCard(
            page,
            "Owner Setup",
            [
                ("Setup", "complete" if setup_status.setup_completed else "incomplete"),
                ("Local config", "loaded" if setup_status.local_config_loaded else "not loaded"),
                ("Owner profile", "configured" if setup_status.owner_name_configured else "pending"),
                ("Owner email", "configured" if setup_status.owner_email_configured else "optional / pending"),
            ],
            accent=ds.SAFEDESK_NEUTRAL,
        ).grid(row=2, column=1, sticky="nsew", padx=(8, 4), pady=6)

        StatusCard(
            page,
            "Biometric Foundation",
            [
                ("Owner face registration", "completed" if registration_status.registration_complete else "pending"),
                ("Owner samples", f"{registration_status.sample_count} saved / {registration_status.required_sample_count} required"),
                ("Recognition demo", "ready" if recognition_ready else "not ready"),
                ("Recognition model", str(recognition_config.get("model_name", "ArcFace"))),
            ],
            accent=ds.SAFEDESK_ALERT,
        ).grid(row=3, column=0, sticky="nsew", padx=(4, 8), pady=6)

        StatusCard(
            page,
            "Safety Boundary",
            [
                ("Real email", "enabled" if context.settings.real_email_enabled else "disabled"),
                ("Real shutdown", "enabled" if context.settings.real_shutdown_enabled else "disabled"),
                ("Real lockdown", "enabled" if context.settings.real_lockdown_enabled else "disabled"),
                ("Final unlock", "not implemented"),
            ],
            accent=ds.SAFEDESK_DEEP_RED,
        ).grid(row=3, column=1, sticky="nsew", padx=(8, 4), pady=6)

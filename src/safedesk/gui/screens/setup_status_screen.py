"""Setup status placeholder screen."""

import customtkinter as ctk

from safedesk.alerts.email_sender import build_email_settings_status
from safedesk.app.application import RuntimeContext
from safedesk.auth.authentication_service import AuthenticationService
from safedesk.config.setup_state import get_setup_status
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.gui.components.status_card import StatusCard
from safedesk.intruders.intruder_manifest import build_intruder_capture_status
from safedesk.logging.event_logger import build_logger_from_config
from safedesk.storage.paths import project_root
from safedesk.threats import ThreatManager
from safedesk.vision.owner_manifest import build_registration_status


class SetupStatusScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        setup_status = get_setup_status(context.load_result.config, context.load_result, context.env)
        owner_registration = context.load_result.config.get("owner_face_registration", {})
        samples_dir = project_root() / owner_registration.get("samples_dir", "data/owner/samples")
        manifest_path = project_root() / owner_registration.get("manifest_path", "data/config/owner_registration_manifest.json")
        required_samples = int(owner_registration.get("required_samples", 5))
        registration_status = build_registration_status(samples_dir, manifest_path, required_samples)
        recognition_config = context.load_result.config.get("owner_recognition", {})
        recognition_required = int(recognition_config.get("minimum_samples_required", 5))
        recognition_ready = registration_status.sample_count >= recognition_required
        liveness_config = context.load_result.config.get("liveness", {})
        intruder_config = context.load_result.config.get("intruder_detection", {})
        intruder_status = build_intruder_capture_status(
            project_root() / intruder_config.get("intruder_images_dir", "data/intruders"),
            project_root() / intruder_config.get("manifest_path", "data/config/intruder_capture_manifest.json"),
            enabled=intruder_config.get("enabled", True),
            demo_only=intruder_config.get("demo_only", True),
        )
        auth_status = AuthenticationService(context.load_result.config).build_status()
        otp_config = context.load_result.config.get("otp", {})
        email_status = build_email_settings_status(context.env, context.load_result.config, context.settings)
        log_status = build_logger_from_config(context.load_result.config).store.build_status(
            enabled=context.load_result.config.get("logging", {}).get("enabled", True)
        )
        threat_manager = ThreatManager(context.load_result.config)
        threat_state = threat_manager.load_state()
        threat_config = context.load_result.config.get("threat_levels", {})
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self)
        page.grid(row=0, column=0, sticky="nsew")
        for column in (0, 1):
            page.grid_columnconfigure(column, weight=1, uniform="setup_status")

        PageHeader(
            page,
            "Setup Status",
            "Review local setup, sample registration, and future authentication readiness without starting camera or recognition.",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 12))

        InfoBanner(
            page,
            "This page reads local configuration and registration metadata only. It does not run DeepFace, TensorFlow, camera capture, or verification.",
            kind="neutral",
            compact=True,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 12))

        StatusCard(
            page,
            "Setup Readiness",
            [
                ("Setup completed", "yes" if setup_status.setup_completed else "no"),
                ("Local config loaded", "yes" if setup_status.local_config_loaded else "no"),
                (".env loaded", "yes" if setup_status.env_loaded else "no"),
                ("Demo/safe mode", "enabled" if setup_status.demo_safe_mode_enabled else "disabled"),
            ],
            accent=ds.SAFEDESK_NEUTRAL,
        ).grid(row=2, column=0, sticky="nsew", padx=(4, 8), pady=6)

        StatusCard(
            page,
            "Owner Setup",
            [
                ("Owner name configured", "yes" if setup_status.owner_name_configured else "no"),
                ("Owner email configured", "yes" if setup_status.owner_email_configured else "no"),
                (
                    "Owner face registration",
                    "completed" if registration_status.registration_complete else "pending",
                ),
                ("Owner face samples", f"{registration_status.sample_count} saved / {registration_status.required_sample_count} required"),
            ],
            accent=ds.SAFEDESK_RED,
        ).grid(row=2, column=1, sticky="nsew", padx=(8, 4), pady=6)

        StatusCard(
            page,
            "Recognition Readiness",
            [
                ("Recognition demo", "ready" if recognition_ready else "not ready"),
                ("Recognition samples", f"{registration_status.sample_count} saved / {recognition_required} required"),
                ("Recognition model", str(recognition_config.get("model_name", "ArcFace"))),
                ("Recognition detector", str(recognition_config.get("detector_backend", "retinaface"))),
                ("Liveness demo", "available" if liveness_config.get("enabled", True) else "disabled"),
                ("Liveness mode", "demo only" if liveness_config.get("demo_only", True) else "review required"),
                ("Intruder detection", "available" if intruder_status.enabled else "disabled"),
                ("Intruder evidence", f"{intruder_status.image_count} saved locally"),
                ("Intruder mode", "demo / foundation only" if intruder_status.demo_only else "review required"),
                ("Threat foundation", "available" if threat_config.get("foundation_enabled", True) else "disabled"),
                ("Threat mode", "demo / foundation only" if threat_config.get("demo_only", True) else "review required"),
                ("Current threat level", str(threat_state.current_level)),
                ("Highest threat level", str(threat_state.highest_level)),
                ("Shutdown candidate", "yes / no shutdown performed" if threat_state.current_level >= 5 else "no"),
            ],
            accent=ds.SAFEDESK_ALERT,
        ).grid(row=3, column=0, sticky="nsew", padx=(4, 8), pady=6)

        StatusCard(
            page,
            "Future Authentication",
            [
                ("Master password", "configured" if auth_status.master_password_configured else "pending"),
                ("Panic code", "configured" if auth_status.panic_code_configured else "pending"),
                ("Auth mode", "foundation only" if auth_status.demo_only else "review required"),
                ("OTP foundation", "available" if otp_config.get("otp_foundation_enabled", True) else "disabled"),
                ("OTP receiver", "configured" if email_status.receiver_configured else "missing"),
                ("Email app password", "present" if email_status.app_password_present else "missing"),
                ("Event logging", "enabled" if log_status.enabled else "disabled"),
                ("Stored events", str(log_status.event_count)),
                ("Final unlock", "not implemented"),
                ("Protected mode", "not active"),
            ],
            accent=ds.TEXT_MUTED,
        ).grid(row=3, column=1, sticky="nsew", padx=(8, 4), pady=6)

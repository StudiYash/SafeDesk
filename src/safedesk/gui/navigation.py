"""Navigation metadata for the SafeDesk GUI shell."""

from dataclasses import dataclass

LAUNCH = "launch"
ADMIN_GATE = "admin_gate"
ADMIN_CONSOLE = "admin_console"
PUBLIC_LOCK = "public_lock"
BACKGROUND_AGENT = "background_agent"

HOME = "home"
SETUP_WIZARD = "setup_wizard"
SETUP_STATUS = "setup_status"
OWNER_FACE_REGISTRATION = "owner_face_registration"
FACE_RECOGNITION_DEMO = "face_recognition_demo"
LIVENESS_DEMO = "liveness_demo"
AUTHENTICATION_SETUP = "authentication_setup"
OTP_EMAIL_SETUP = "otp_email_setup"
EVENT_LOGS = "event_logs"
INTRUDER_DETECTION_DEMO = "intruder_detection_demo"
INTRUDER_HISTORY = "intruder_history"
THREAT_LEVEL_DEMO = "threat_level_demo"
PROTECTED_MODE_PREVIEW = "protected_mode_preview"
SHUTDOWN_ESCALATION = "shutdown_escalation"
ALARM_SYSTEM = "alarm_system"
DASHBOARD = "dashboard"
SETTINGS = "settings"
ABOUT = "about"


@dataclass(frozen=True)
class ScreenDefinition:
    name: str
    label: str
    description: str


SCREEN_DEFINITIONS = (
    ScreenDefinition(HOME, "Home", "SafeDesk GUI shell overview."),
    ScreenDefinition(SETUP_WIZARD, "Setup Wizard", "Safe first-time setup placeholder."),
    ScreenDefinition(SETUP_STATUS, "Setup Status", "Configuration and readiness placeholders."),
    ScreenDefinition(OWNER_FACE_REGISTRATION, "Owner Face Registration", "Local owner sample capture foundation."),
    ScreenDefinition(FACE_RECOGNITION_DEMO, "Face Recognition Demo", "Local owner recognition demo."),
    ScreenDefinition(LIVENESS_DEMO, "Liveness Demo", "Basic movement challenge demo foundation."),
    ScreenDefinition(AUTHENTICATION_SETUP, "Authentication Setup", "Local password and panic-code foundation."),
    ScreenDefinition(OTP_EMAIL_SETUP, "OTP & Email Setup", "Manual OTP and email foundation."),
    ScreenDefinition(EVENT_LOGS, "Event Logs", "Local SQLite event log dashboard."),
    ScreenDefinition(INTRUDER_DETECTION_DEMO, "Intruder Detection Demo", "Manual unknown/unverified evidence capture foundation."),
    ScreenDefinition(INTRUDER_HISTORY, "Intruder History", "Owner-only local intruder evidence review."),
    ScreenDefinition(THREAT_LEVEL_DEMO, "Threat Level Demo", "Manual threat-level simulation foundation."),
    ScreenDefinition(PROTECTED_MODE_PREVIEW, "Protected Mode Demo", "Safe protected-mode foundation simulator."),
    ScreenDefinition(SHUTDOWN_ESCALATION, "Shutdown Escalation Demo", "Dry-run shutdown escalation foundation."),
    ScreenDefinition(ALARM_SYSTEM, "Alarm System", "Owner-controlled demo-safe alarm preview and status."),
    ScreenDefinition(DASHBOARD, "Dashboard", "Owner-only SafeDesk status and recent activity overview."),
    ScreenDefinition(SETTINGS, "Settings", "Future settings placeholder."),
    ScreenDefinition(ABOUT, "About", "Project information."),
)

SCREEN_NAMES = tuple(screen.name for screen in SCREEN_DEFINITIONS)

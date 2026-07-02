"""Navigation metadata for the SafeDesk GUI shell."""

from dataclasses import dataclass

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
PROTECTED_MODE_PREVIEW = "protected_mode_preview"
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
    ScreenDefinition(PROTECTED_MODE_PREVIEW, "Protected Preview", "Non-operational protected mode preview."),
    ScreenDefinition(DASHBOARD, "Dashboard", "Future intruder history and logs placeholder."),
    ScreenDefinition(SETTINGS, "Settings", "Future settings placeholder."),
    ScreenDefinition(ABOUT, "About", "Project information."),
)

SCREEN_NAMES = tuple(screen.name for screen in SCREEN_DEFINITIONS)

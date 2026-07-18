"""Navigation metadata and guarded sidebar organization for SafeDesk."""

from __future__ import annotations

from dataclasses import dataclass

from safedesk.developer_tools import DeveloperToolsPolicy

LAUNCH = "launch"
ADMIN_GATE = "admin_gate"
ADMIN_CONSOLE = "admin_console"
PUBLIC_LOCK = "public_lock"
BACKGROUND_AGENT = "background_agent"

HOME = "home"
DASHBOARD = "dashboard"
SETUP_STATUS = "setup_status"
OWNER_FACE_REGISTRATION = "owner_face_registration"
AUTHENTICATION_SETUP = "authentication_setup"
EVENT_LOGS = "event_logs"
INTRUDER_HISTORY = "intruder_history"
ALARM_SYSTEM = "alarm_system"
DEVELOPER_TOOLS = "developer_tools"
SETTINGS = "settings"
ABOUT = "about"

SETUP_WIZARD = "setup_wizard"
FACE_RECOGNITION_DEMO = "face_recognition_demo"
LIVENESS_DEMO = "liveness_demo"
OTP_EMAIL_SETUP = "otp_email_setup"
INTRUDER_DETECTION_DEMO = "intruder_detection_demo"
THREAT_LEVEL_DEMO = "threat_level_demo"
PROTECTED_MODE_PREVIEW = "protected_mode_preview"
SHUTDOWN_ESCALATION = "shutdown_escalation"

OVERVIEW_SECTION = "Overview"
OWNER_SETUP_SECTION = "Owner & Setup"
SECURITY_ACTIVITY_SECTION = "Security Activity"
DEVELOPER_SECTION = "Developer"
SYSTEM_SECTION = "System"
SIDEBAR_SECTION_ORDER = (
    OVERVIEW_SECTION,
    OWNER_SETUP_SECTION,
    SECURITY_ACTIVITY_SECTION,
    DEVELOPER_SECTION,
    SYSTEM_SECTION,
)

DEVELOPER_ROUTE_NAMES = frozenset(
    {
        SETUP_WIZARD,
        FACE_RECOGNITION_DEMO,
        LIVENESS_DEMO,
        OTP_EMAIL_SETUP,
        INTRUDER_DETECTION_DEMO,
        THREAT_LEVEL_DEMO,
        PROTECTED_MODE_PREVIEW,
        SHUTDOWN_ESCALATION,
    }
)


@dataclass(frozen=True)
class ScreenDefinition:
    name: str
    label: str
    description: str
    section: str = ""
    developer_only: bool = False
    show_in_sidebar: bool = True


SCREEN_DEFINITIONS = (
    ScreenDefinition(HOME, "Home", "SafeDesk GUI shell overview.", OVERVIEW_SECTION),
    ScreenDefinition(DASHBOARD, "Dashboard", "Owner-only SafeDesk status and recent activity overview.", OVERVIEW_SECTION),
    ScreenDefinition(SETUP_STATUS, "Setup Status", "Configuration and readiness overview.", OWNER_SETUP_SECTION),
    ScreenDefinition(OWNER_FACE_REGISTRATION, "Owner Face Registration", "Local owner sample capture foundation.", OWNER_SETUP_SECTION),
    ScreenDefinition(AUTHENTICATION_SETUP, "Authentication Setup", "Local password and panic-code foundation.", OWNER_SETUP_SECTION),
    ScreenDefinition(EVENT_LOGS, "Event Logs", "Local SQLite event log dashboard.", SECURITY_ACTIVITY_SECTION),
    ScreenDefinition(INTRUDER_HISTORY, "Intruder History", "Owner-only local intruder evidence review.", SECURITY_ACTIVITY_SECTION),
    ScreenDefinition(ALARM_SYSTEM, "Alarm System", "Owner-controlled demo-safe alarm preview and status.", SECURITY_ACTIVITY_SECTION),
    ScreenDefinition(DEVELOPER_TOOLS, "Developer Tools", "Guarded demo and diagnostic tools.", DEVELOPER_SECTION, True),
    ScreenDefinition(SETTINGS, "Settings", "Approved local SafeDesk preferences.", SYSTEM_SECTION),
    ScreenDefinition(ABOUT, "About", "Project information.", SYSTEM_SECTION),
    ScreenDefinition(SETUP_WIZARD, "Setup Wizard", "Safe first-time setup demo.", developer_only=True, show_in_sidebar=False),
    ScreenDefinition(FACE_RECOGNITION_DEMO, "Face Recognition Demo", "Local owner recognition demo.", developer_only=True, show_in_sidebar=False),
    ScreenDefinition(LIVENESS_DEMO, "Liveness Demo", "Basic movement challenge demo foundation.", developer_only=True, show_in_sidebar=False),
    ScreenDefinition(OTP_EMAIL_SETUP, "OTP & Email Setup", "Manual OTP and email foundation.", developer_only=True, show_in_sidebar=False),
    ScreenDefinition(INTRUDER_DETECTION_DEMO, "Intruder Detection Demo", "Manual unknown evidence capture foundation.", developer_only=True, show_in_sidebar=False),
    ScreenDefinition(THREAT_LEVEL_DEMO, "Threat Level Demo", "Manual threat-level simulation foundation.", developer_only=True, show_in_sidebar=False),
    ScreenDefinition(PROTECTED_MODE_PREVIEW, "Protected Mode Demo", "Safe protected-mode foundation simulator.", developer_only=True, show_in_sidebar=False),
    ScreenDefinition(SHUTDOWN_ESCALATION, "Shutdown Escalation Demo", "Dry-run shutdown escalation foundation.", developer_only=True, show_in_sidebar=False),
)

SCREEN_NAMES = tuple(screen.name for screen in SCREEN_DEFINITIONS)
SCREEN_DEFINITION_BY_NAME = {screen.name: screen for screen in SCREEN_DEFINITIONS}


def visible_sidebar_sections(
    config: dict,
    *,
    effective_environment: str | None = None,
) -> tuple[tuple[str, tuple[ScreenDefinition, ...]], ...]:
    """Return grouped owner navigation permitted by the startup policy."""

    developer_visible = DeveloperToolsPolicy(
        config,
        effective_environment=effective_environment,
    ).landing_page_visible()
    sections: list[tuple[str, tuple[ScreenDefinition, ...]]] = []
    for section_name in SIDEBAR_SECTION_ORDER:
        screens = tuple(
            screen
            for screen in SCREEN_DEFINITIONS
            if screen.section == section_name
            and screen.show_in_sidebar
            and (screen.name != DEVELOPER_TOOLS or developer_visible)
        )
        if screens:
            sections.append((section_name, screens))
    return tuple(sections)


def admin_route_allowed(
    config: dict,
    screen_name: str,
    *,
    effective_environment: str | None = None,
) -> bool:
    """Return whether an internal Admin Console route passes startup policy."""

    if screen_name not in SCREEN_NAMES:
        return False
    status = DeveloperToolsPolicy(
        config,
        effective_environment=effective_environment,
    ).build_status()
    if screen_name in DEVELOPER_ROUTE_NAMES:
        return status.demo_routes_allowed
    if screen_name == DEVELOPER_TOOLS:
        return status.landing_visible
    return True

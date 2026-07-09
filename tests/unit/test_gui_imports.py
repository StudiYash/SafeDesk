from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import (
    ABOUT,
    ADMIN_CONSOLE,
    ADMIN_GATE,
    AUTHENTICATION_SETUP,
    BACKGROUND_AGENT,
    DASHBOARD,
    EVENT_LOGS,
    FACE_RECOGNITION_DEMO,
    HOME,
    INTRUDER_DETECTION_DEMO,
    LAUNCH,
    LIVENESS_DEMO,
    OWNER_FACE_REGISTRATION,
    OTP_EMAIL_SETUP,
    PROTECTED_MODE_PREVIEW,
    PUBLIC_LOCK,
    SCREEN_NAMES,
    SETUP_STATUS,
    SETUP_WIZARD,
    SETTINGS,
    SHUTDOWN_ESCALATION,
    THREAT_LEVEL_DEMO,
)


def test_navigation_metadata_contains_expected_screens():
    assert LAUNCH == "launch"
    assert ADMIN_GATE == "admin_gate"
    assert ADMIN_CONSOLE == "admin_console"
    assert PUBLIC_LOCK == "public_lock"
    assert BACKGROUND_AGENT == "background_agent"
    assert set(SCREEN_NAMES) == {
        HOME,
        SETUP_WIZARD,
        SETUP_STATUS,
        OWNER_FACE_REGISTRATION,
        FACE_RECOGNITION_DEMO,
        LIVENESS_DEMO,
        AUTHENTICATION_SETUP,
        OTP_EMAIL_SETUP,
        EVENT_LOGS,
        INTRUDER_DETECTION_DEMO,
        THREAT_LEVEL_DEMO,
        PROTECTED_MODE_PREVIEW,
        SHUTDOWN_ESCALATION,
        DASHBOARD,
        SETTINGS,
        ABOUT,
    }


def test_gui_modules_import_without_opening_window():
    import pytest

    pytest.importorskip("customtkinter")

    import safedesk.gui.design_system
    import safedesk.gui.main_window
    import safedesk.gui.theme
    from safedesk.gui.components import InfoBanner, PageHeader, ScrollablePage, SidebarButton, StatusCard
    from safedesk.gui.screens.launch_screen import LaunchScreen
    from safedesk.gui.screens.public_lock_screen import PublicLockScreen
    from safedesk.gui.screens.admin_gate_screen import AdminGateScreen

    assert safedesk.gui.main_window.SafeDeskMainWindow is not None
    assert safedesk.gui.theme.apply_theme is not None
    assert safedesk.gui.design_system.SAFEDESK_RED == "#B61D18"
    assert InfoBanner is not None
    assert PageHeader is not None
    assert ScrollablePage is not None
    assert SidebarButton is not None
    assert StatusCard is not None
    assert LaunchScreen is not None
    assert PublicLockScreen is not None
    assert AdminGateScreen is not None

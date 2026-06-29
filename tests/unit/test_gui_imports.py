from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import (
    ABOUT,
    AUTHENTICATION_SETUP,
    DASHBOARD,
    FACE_RECOGNITION_DEMO,
    HOME,
    LIVENESS_DEMO,
    OWNER_FACE_REGISTRATION,
    OTP_EMAIL_SETUP,
    PROTECTED_MODE_PREVIEW,
    SCREEN_NAMES,
    SETUP_STATUS,
    SETUP_WIZARD,
    SETTINGS,
)


def test_navigation_metadata_contains_expected_screens():
    assert set(SCREEN_NAMES) == {
        HOME,
        SETUP_WIZARD,
        SETUP_STATUS,
        OWNER_FACE_REGISTRATION,
        FACE_RECOGNITION_DEMO,
        LIVENESS_DEMO,
        AUTHENTICATION_SETUP,
        OTP_EMAIL_SETUP,
        PROTECTED_MODE_PREVIEW,
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

    assert safedesk.gui.main_window.SafeDeskMainWindow is not None
    assert safedesk.gui.theme.apply_theme is not None
    assert safedesk.gui.design_system.SAFEDESK_RED == "#B61D18"
    assert InfoBanner is not None
    assert PageHeader is not None
    assert ScrollablePage is not None
    assert SidebarButton is not None
    assert StatusCard is not None

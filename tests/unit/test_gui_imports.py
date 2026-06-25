from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import (
    ABOUT,
    DASHBOARD,
    HOME,
    PROTECTED_MODE_PREVIEW,
    SCREEN_NAMES,
    SETUP_STATUS,
    SETTINGS,
)


def test_navigation_metadata_contains_expected_screens():
    assert set(SCREEN_NAMES) == {
        HOME,
        SETUP_STATUS,
        PROTECTED_MODE_PREVIEW,
        DASHBOARD,
        SETTINGS,
        ABOUT,
    }


def test_gui_modules_import_without_opening_window():
    import safedesk.gui.main_window
    import safedesk.gui.theme

    assert safedesk.gui.main_window.SafeDeskMainWindow is not None
    assert safedesk.gui.theme.apply_theme is not None

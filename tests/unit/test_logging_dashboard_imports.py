from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import EVENT_LOGS, SCREEN_NAMES


def test_navigation_metadata_includes_event_logs():
    assert EVENT_LOGS in SCREEN_NAMES


def test_logging_dashboard_imports_without_opening_window():
    pytest.importorskip("customtkinter")

    import safedesk.gui.screens.logging_dashboard_screen

    assert safedesk.gui.screens.logging_dashboard_screen.LoggingDashboardScreen is not None

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


def test_logging_dashboard_uses_bounded_pagination_and_async_clear_source():
    source = (SRC / "safedesk" / "gui" / "screens" / "logging_dashboard_screen.py").read_text(encoding="utf-8")

    assert "EVENT_LOG_PAGE_SIZE = 50" in source
    assert "MAX_EVENT_PAGE_SIZE" in source
    assert "list_event_page(" in source
    assert ".list_events()" not in source
    assert 'text="Previous"' in source
    assert 'text="Next"' in source
    assert "_clear_in_progress" in source
    assert "Thread(target=self._clear_events_worker, daemon=True)" in source
    assert "Queue" in source
    assert "release_resources" in source
    assert "resume_resources" in source
    assert "VACUUM" not in source

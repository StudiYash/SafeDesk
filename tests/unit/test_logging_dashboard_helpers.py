from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.logging.dashboard_helpers import (
    apply_event_filters,
    event_matches_search,
    filter_search_sort_events,
    format_event_timestamp_for_display,
    sort_events,
)
from safedesk.logging.log_models import SafeDeskEvent


def _event(number: int, **kwargs) -> SafeDeskEvent:
    defaults = {
        "category": "app",
        "action": f"action_{number}",
        "status": "info",
        "severity": "INFO",
        "message": f"Message {number}",
        "source": "gui",
        "timestamp": f"2026-06-30T10:00:0{number}+00:00",
        "event_number": number,
        "metadata": {},
    }
    defaults.update(kwargs)
    return SafeDeskEvent(**defaults)


def test_format_event_timestamp_for_display_returns_local_pattern():
    display = format_event_timestamp_for_display("2026-06-30T22:45:12+00:00")

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}", display)


def test_format_event_timestamp_for_display_handles_invalid_input():
    assert format_event_timestamp_for_display("not a timestamp") == "invalid timestamp"


def test_filtering_by_category_status_and_severity():
    events = [
        _event(1, category="otp", status="failed", severity="WARNING"),
        _event(2, category="app", status="info", severity="INFO"),
    ]

    filtered = apply_event_filters(events, {"category": "otp", "status": "failed", "severity": "WARNING"})

    assert [event.event_number for event in filtered] == [1]


def test_search_matches_category_action_status_message_source_and_event_number():
    event = _event(
        7,
        category="authentication",
        action="master_password_verification",
        status="failed",
        message="Master Password not verified",
        source="gui",
        metadata={"attempts_remaining": 2},
    )

    for query in ("authentication", "master_password", "failed", "not verified", "gui", "7", "attempts_remaining"):
        assert event_matches_search(event, query) is True


def test_search_applies_after_filtering():
    events = [
        _event(1, category="otp", action="otp_verification", status="failed"),
        _event(2, category="authentication", action="master_password_verification", status="failed"),
    ]

    visible = filter_search_sort_events(
        events,
        filters={"category": "otp"},
        query="failed",
        sort_field="Event Number",
        direction="Ascending",
    )

    assert [event.event_number for event in visible] == [1]


def test_sorting_keeps_stable_event_numbers():
    events = [
        _event(1, category="otp", timestamp="2026-06-30T10:00:00+00:00"),
        _event(2, category="app", timestamp="2026-06-30T11:00:00+00:00"),
    ]

    sorted_by_timestamp = sort_events(events, "Timestamp", "Descending")
    sorted_by_category = sort_events(events, "Category", "Ascending")

    assert [event.event_number for event in sorted_by_timestamp] == [2, 1]
    assert [event.event_number for event in sorted_by_category] == [2, 1]

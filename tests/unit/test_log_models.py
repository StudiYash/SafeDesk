from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.logging.log_models import EVENT_CATEGORIES, EVENT_SEVERITIES, EVENT_STATUSES, SafeDeskEvent


def test_safe_desk_event_defaults_are_safe_and_present():
    event = SafeDeskEvent(category="app", action="startup", status="info")

    assert event.event_id
    assert event.timestamp
    assert event.severity == "INFO"
    assert event.metadata == {}
    assert event.source == "gui"
    assert event.session_id == "local"
    assert event.event_number == 0


def test_log_model_constants_include_phase_11_categories():
    assert "authentication" in EVENT_CATEGORIES
    assert "otp" in EVENT_CATEGORIES
    assert "email" in EVENT_CATEGORIES
    assert "intruder_detection" in EVENT_CATEGORIES
    assert "threat_level" in EVENT_CATEGORIES
    assert "success" in EVENT_STATUSES
    assert "blocked" in EVENT_STATUSES
    assert "WARNING" in EVENT_SEVERITIES

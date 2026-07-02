from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.threats.threat_manager import ThreatManager


def _config_for(tmp_path):
    return deep_merge(
        DEFAULT_CONFIG,
        {
            "threat_levels": {
                "state_path": str(tmp_path / "threat_state.json"),
                "repeated_unknown_threshold": 3,
                "failed_password_threshold": 3,
                "failed_otp_threshold": 3,
                "forceful_attempt_threshold": 3,
                "forced_exit_threshold": 1,
            },
            "logging": {
                "enabled": True,
                "database_path": str(tmp_path / "safedesk.sqlite3"),
                "demo_only": True,
            },
        },
    )


def test_unknown_unverified_face_reaches_level_one(tmp_path):
    manager = ThreatManager(_config_for(tmp_path))

    result = manager.record_event("unknown_unverified_face")

    assert result.success is True
    assert result.new_level == 1
    assert result.state.unknown_unverified_count == 1


def test_repeated_unknown_unverified_face_reaches_level_two(tmp_path):
    manager = ThreatManager(_config_for(tmp_path))

    manager.record_event("unknown_unverified_face")
    manager.record_event("unknown_unverified_face")
    result = manager.record_event("unknown_unverified_face")

    assert result.new_level == 2
    assert result.state.unknown_unverified_count == 3


def test_failed_password_threshold_reaches_level_three(tmp_path):
    manager = ThreatManager(_config_for(tmp_path))

    manager.record_event("failed_password_attempt")
    manager.record_event("failed_password_attempt")
    result = manager.record_event("failed_password_attempt")

    assert result.new_level == 3
    assert result.state.failed_password_count == 3


def test_mixed_failed_auth_attempts_reach_forceful_candidate_level_four(tmp_path):
    manager = ThreatManager(_config_for(tmp_path))

    manager.record_event("failed_password_attempt")
    manager.record_event("failed_otp_attempt")
    result = manager.record_event("failed_panic_attempt")

    assert result.new_level == 4
    assert result.reason == "Combined failed authentication simulations reached the forceful-access candidate threshold."


def test_forced_exit_reaches_level_four(tmp_path):
    manager = ThreatManager(_config_for(tmp_path))

    result = manager.record_event("forced_exit_attempt")

    assert result.new_level == 4
    assert result.state.forced_exit_count == 1


def test_serious_follow_up_can_reach_level_five_without_shutdown(tmp_path):
    manager = ThreatManager(_config_for(tmp_path))

    manager.record_event("forced_exit_attempt")
    result = manager.record_event("serious_follow_up_event")

    assert result.new_level == 5
    assert "No shutdown was performed." in result.message


def test_reset_returns_level_zero(tmp_path):
    manager = ThreatManager(_config_for(tmp_path))
    manager.record_event("forced_exit_attempt")

    result = manager.reset_state()

    assert result.status == "reset"
    assert result.new_level == 0
    assert manager.load_state().current_level == 0


def test_unknown_event_is_rejected_without_state_change(tmp_path):
    manager = ThreatManager(_config_for(tmp_path))

    result = manager.record_event("not_a_supported_event")

    assert result.success is False
    assert result.status == "invalid_event"
    assert manager.load_state().current_level == 0


def test_threat_events_are_logged_with_safe_category_and_metadata(tmp_path):
    manager = ThreatManager(_config_for(tmp_path))

    manager.record_event("failed_password_attempt")
    manager.record_event("failed_otp_attempt")
    manager.record_event("failed_panic_attempt")
    manager.record_event("forced_exit_attempt")
    events = manager.event_logger.store.list_events()

    assert any(event.category == "threat_level" for event in events)
    assert all("shutdown_performed" in event.metadata for event in events)
    assert all(event.metadata["shutdown_performed"] is False for event in events)
    assert any(event.metadata.get("failed_password_count") == 1 for event in events)
    assert any(event.metadata.get("failed_otp_count") == 1 for event in events)
    assert any(event.metadata.get("failed_panic_count") == 1 for event in events)

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.protected_mode.protected_manager import ProtectedModeManager
from safedesk.threats.threat_manager import ThreatManager


def _config_for(tmp_path):
    return deep_merge(
        DEFAULT_CONFIG,
        {
            "protected_mode": {
                "state_path": str(tmp_path / "protected_mode_state.json"),
                "activation_candidate_threat_level": 4,
                "shutdown_candidate_threat_level": 5,
            },
            "threat_levels": {
                "state_path": str(tmp_path / "threat_state.json"),
            },
            "logging": {
                "enabled": True,
                "database_path": str(tmp_path / "safedesk.sqlite3"),
                "demo_only": True,
            },
        },
    )


def test_arm_action_reaches_armed_state(tmp_path):
    manager = ProtectedModeManager(_config_for(tmp_path))

    result = manager.perform_action("arm")

    assert result.success is True
    assert result.new_mode == "armed"
    assert result.state.armed is True
    assert result.state.lockdown_performed is False
    assert result.state.shutdown_performed is False


def test_activate_demo_action_reaches_active_demo_state(tmp_path):
    manager = ProtectedModeManager(_config_for(tmp_path))

    result = manager.perform_action("activate_demo")

    assert result.new_mode == "active_demo"
    assert result.state.active_demo is True
    assert "No lockdown was performed" in result.message


def test_mark_recovery_required_reaches_recovery_required_state(tmp_path):
    manager = ProtectedModeManager(_config_for(tmp_path))

    result = manager.perform_action("mark_recovery_required")

    assert result.new_mode == "recovery_required"
    assert result.state.recovery_required is True


def test_recovery_success_clears_recovery_required(tmp_path):
    manager = ProtectedModeManager(_config_for(tmp_path))
    manager.perform_action("mark_recovery_required")

    result = manager.perform_action("simulate_recovery_success")

    assert result.new_mode == "recovery_successful"
    assert result.state.recovery_required is False
    assert result.state.active_demo is False


def test_recovery_failure_does_not_perform_shutdown_or_lockdown(tmp_path):
    manager = ProtectedModeManager(_config_for(tmp_path))

    result = manager.perform_action("simulate_recovery_failure")

    assert result.new_mode == "recovery_required"
    assert result.state.lockdown_performed is False
    assert result.state.shutdown_performed is False
    assert "No shutdown or lockdown was performed" in result.message


def test_apply_threat_recommendation_reads_tmp_threat_state_and_marks_shutdown_candidate(tmp_path):
    config = _config_for(tmp_path)
    threat_manager = ThreatManager(config)
    threat_manager.record_event("forced_exit_attempt")
    threat_manager.record_event("serious_follow_up_event")
    manager = ProtectedModeManager(config)

    result = manager.perform_action("apply_threat_recommendation")

    assert result.new_mode == "armed"
    assert result.state.threat_level_at_last_update == 5
    assert result.state.shutdown_candidate is True
    assert result.state.shutdown_performed is False
    assert "No shutdown was performed" in result.message


def test_reset_returns_inactive_safe_state(tmp_path):
    manager = ProtectedModeManager(_config_for(tmp_path))
    manager.perform_action("activate_demo")

    result = manager.perform_action("reset")

    assert result.status == "reset"
    assert result.new_mode == "inactive"
    assert manager.load_state().active_demo is False


def test_unknown_action_is_rejected_safely(tmp_path):
    manager = ProtectedModeManager(_config_for(tmp_path))

    result = manager.perform_action("not_supported")

    assert result.success is False
    assert result.status == "invalid_action"
    assert manager.load_state().mode == "inactive"


def test_protected_mode_events_log_safe_category_and_false_enforcement_metadata(tmp_path):
    manager = ProtectedModeManager(_config_for(tmp_path))

    manager.perform_action("activate_demo")
    events = manager.event_logger.store.list_events()

    assert any(event.category == "protected_mode" for event in events)
    assert all(event.metadata["lockdown_performed"] is False for event in events)
    assert all(event.metadata["shutdown_performed"] is False for event in events)
    assert all(event.metadata["protected_enforcement_active"] is False for event in events)

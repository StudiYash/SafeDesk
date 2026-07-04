from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.shutdown_escalation.shutdown_models import SHUTDOWN_ACTIONS, SHUTDOWN_ESCALATION_STATES, ShutdownEscalationState


def test_shutdown_state_defaults_are_safe():
    state = ShutdownEscalationState()

    assert state.mode == "idle"
    assert state.demo_only is True
    assert state.real_shutdown_enabled is False
    assert state.real_shutdown_command_enabled is False
    assert state.guarded_real_shutdown_ready is False
    assert state.real_shutdown_requested is False
    assert state.real_shutdown_scheduled is False
    assert state.real_shutdown_aborted is False
    assert state.real_shutdown_result_status == "not_requested"
    assert state.shutdown_performed is False
    assert state.restart_performed is False
    assert state.logoff_performed is False
    assert state.lockdown_performed is False
    assert state.alarm_performed is False
    assert state.email_sent is False


def test_shutdown_models_include_required_states_and_actions():
    assert "countdown_running" in SHUTDOWN_ESCALATION_STATES
    assert "simulated_shutdown_completed" in SHUTDOWN_ESCALATION_STATES
    assert "start_demo_countdown" in SHUTDOWN_ACTIONS
    assert "complete_demo_countdown_now" in SHUTDOWN_ACTIONS

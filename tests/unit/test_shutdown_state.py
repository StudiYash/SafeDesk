from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.shutdown_escalation.shutdown_models import ShutdownEscalationState
from safedesk.shutdown_escalation.shutdown_state import load_shutdown_state, save_shutdown_state, shutdown_state_to_dict


def test_missing_shutdown_state_returns_idle_default(tmp_path):
    state = load_shutdown_state(tmp_path / "missing.json")

    assert state.mode == "idle"
    assert state.shutdown_performed is False
    assert state.lockdown_performed is False


def test_corrupt_shutdown_state_returns_idle_default(tmp_path):
    path = tmp_path / "shutdown_state.json"
    path.write_text("{not-json", encoding="utf-8")

    state = load_shutdown_state(path)

    assert state.mode == "idle"
    assert state.countdown_running is False


def test_save_and_load_shutdown_state_uses_safe_fields(tmp_path):
    path = tmp_path / "shutdown_state.json"
    state = ShutdownEscalationState(
        mode="countdown_running",
        shutdown_candidate=True,
        countdown_running=True,
        countdown_remaining_seconds=10,
        countdown_total_seconds=30,
        last_action="start_demo_countdown",
        last_reason="Demo countdown started.",
        updated_at="2026-07-03T12:00:00+00:00",
        threat_level_at_last_update=5,
        protected_mode_at_last_update="active_demo",
        protected_shutdown_candidate=True,
        guarded_real_shutdown_ready=True,
        real_shutdown_confirmation_matched=True,
        real_shutdown_requested=True,
        real_shutdown_scheduled=True,
        real_shutdown_abort_requested=True,
        real_shutdown_aborted=True,
        real_shutdown_countdown_seconds=60,
        real_shutdown_platform="Windows",
        real_shutdown_result_status="scheduled",
        real_shutdown_result_message="Guarded Windows shutdown was scheduled.",
        real_shutdown_enabled=True,
        real_shutdown_command_enabled=True,
        shutdown_performed=True,
    )

    save_shutdown_state(path, state)
    loaded = load_shutdown_state(path)
    raw = path.read_text(encoding="utf-8").lower()

    assert loaded.mode == "countdown_running"
    assert loaded.countdown_remaining_seconds == 10
    assert loaded.protected_shutdown_candidate is True
    assert loaded.guarded_real_shutdown_ready is True
    assert loaded.real_shutdown_scheduled is True
    assert loaded.real_shutdown_aborted is True
    assert loaded.real_shutdown_countdown_seconds == 60
    assert loaded.real_shutdown_result_status == "scheduled"
    assert loaded.real_shutdown_enabled is True
    assert loaded.real_shutdown_command_enabled is True
    assert loaded.shutdown_performed is False
    assert "password" not in raw
    assert "otp" not in raw
    assert "panic" not in raw
    assert "image_path" not in raw
    assert str(tmp_path).lower() not in raw


def test_shutdown_state_dict_does_not_include_private_paths_or_secrets():
    data = shutdown_state_to_dict(ShutdownEscalationState(mode="candidate", shutdown_candidate=True))
    raw = str(data).lower()

    assert "path" not in raw
    assert "password" not in raw
    assert "otp" not in raw
    assert "embedding" not in raw

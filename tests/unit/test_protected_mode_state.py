from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.protected_mode.protected_models import ProtectedModeState
from safedesk.protected_mode.protected_state import (
    load_protected_mode_state,
    protected_mode_state_to_dict,
    save_protected_mode_state,
)


def test_missing_protected_state_returns_inactive_default(tmp_path):
    state = load_protected_mode_state(tmp_path / "missing.json")

    assert state.mode == "inactive"
    assert state.lockdown_performed is False
    assert state.shutdown_performed is False


def test_corrupt_protected_state_returns_inactive_default(tmp_path):
    path = tmp_path / "protected_mode_state.json"
    path.write_text("{not-json", encoding="utf-8")

    state = load_protected_mode_state(path)

    assert state.mode == "inactive"
    assert state.armed is False


def test_save_and_load_protected_state_uses_safe_fields(tmp_path):
    path = tmp_path / "protected_mode_state.json"
    state = ProtectedModeState(
        mode="active_demo",
        armed=True,
        active_demo=True,
        recovery_required=False,
        last_action="activate_demo",
        last_reason="Protected mode demo state activated.",
        updated_at="2026-07-02T12:00:00+00:00",
        threat_level_at_last_update=4,
        shutdown_candidate=True,
    )

    save_protected_mode_state(path, state)
    loaded = load_protected_mode_state(path)
    raw = path.read_text(encoding="utf-8").lower()

    assert loaded.mode == "active_demo"
    assert loaded.active_demo is True
    assert loaded.shutdown_candidate is True
    assert loaded.lockdown_performed is False
    assert loaded.shutdown_performed is False
    assert "password" not in raw
    assert "otp" not in raw
    assert "panic" not in raw
    assert "image_path" not in raw
    assert str(tmp_path).lower() not in raw


def test_protected_state_dict_does_not_include_private_paths_or_secrets():
    data = protected_mode_state_to_dict(ProtectedModeState(mode="armed", armed=True))
    raw = str(data).lower()

    assert "path" not in raw
    assert "password" not in raw
    assert "otp" not in raw
    assert "embedding" not in raw

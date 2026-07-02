from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.threats.threat_models import ThreatState
from safedesk.threats.threat_state import load_threat_state, save_threat_state, threat_state_to_dict


def test_missing_threat_state_returns_level_zero_default(tmp_path):
    state = load_threat_state(tmp_path / "missing_threat_state.json")

    assert state.current_level == 0
    assert state.highest_level == 0
    assert state.demo_only is True


def test_corrupt_threat_state_returns_level_zero_default(tmp_path):
    path = tmp_path / "threat_state.json"
    path.write_text("{not-json", encoding="utf-8")

    state = load_threat_state(path)

    assert state.current_level == 0
    assert state.highest_level == 0


def test_save_and_load_threat_state_uses_safe_fields(tmp_path):
    path = tmp_path / "threat_state.json"
    state = ThreatState(
        current_level=3,
        highest_level=4,
        unknown_unverified_count=2,
        failed_password_count=3,
        failed_otp_count=1,
        failed_panic_count=1,
        forced_exit_count=0,
        last_reason="Failed authentication threshold reached.",
        updated_at="2026-07-02T12:00:00+00:00",
        demo_only=True,
    )

    save_threat_state(path, state)
    loaded = load_threat_state(path)
    raw = path.read_text(encoding="utf-8")

    assert loaded.current_level == 3
    assert loaded.highest_level == 4
    assert loaded.failed_password_count == 3
    assert "password_value" not in raw
    assert "otp_code" not in raw
    assert "image_path" not in raw


def test_threat_state_dict_does_not_include_private_paths_or_secrets():
    data = threat_state_to_dict(ThreatState(current_level=1, highest_level=1))
    raw = str(data).lower()

    assert "path" not in raw
    assert "password_value" not in raw
    assert "otp_code" not in raw
    assert "embedding" not in raw

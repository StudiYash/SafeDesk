from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.threats.threat_models import THREAT_EVENT_TYPES, THREAT_LEVEL_DEFINITIONS, ThreatState


def test_threat_level_definitions_use_safe_foundation_wording():
    titles = {definition.level: definition.title for definition in THREAT_LEVEL_DEFINITIONS}

    assert titles[0] == "Safe / idle"
    assert titles[5] == "Shutdown escalation candidate"
    assert "candidate" in titles[5].lower()


def test_supported_threat_event_types_include_manual_simulations():
    assert "unknown_unverified_face" in THREAT_EVENT_TYPES
    assert "failed_password_attempt" in THREAT_EVENT_TYPES
    assert "failed_otp_attempt" in THREAT_EVENT_TYPES
    assert "failed_panic_attempt" in THREAT_EVENT_TYPES
    assert "forced_exit_attempt" in THREAT_EVENT_TYPES
    assert "serious_follow_up_event" in THREAT_EVENT_TYPES


def test_threat_state_defaults_are_safe():
    state = ThreatState()

    assert state.current_level == 0
    assert state.highest_level == 0
    assert state.demo_only is True

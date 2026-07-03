from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.protected_mode.protected_models import PROTECTED_MODE_DEFINITIONS, PROTECTED_MODE_STATES, ProtectedModeState


def test_protected_mode_states_include_phase_14_foundation_modes():
    assert PROTECTED_MODE_STATES == (
        "inactive",
        "armed",
        "active_demo",
        "recovery_required",
        "recovery_successful",
        "reset",
    )


def test_protected_mode_definitions_use_safe_wording():
    definitions = {definition.mode: definition.description for definition in PROTECTED_MODE_DEFINITIONS}

    assert "No enforcement" in definitions["active_demo"]
    assert "No lock screen" in definitions["recovery_required"]


def test_protected_mode_state_defaults_are_safe():
    state = ProtectedModeState()

    assert state.mode == "inactive"
    assert state.lockdown_performed is False
    assert state.shutdown_performed is False
    assert state.demo_only is True

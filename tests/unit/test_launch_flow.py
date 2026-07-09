from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.app_modes import AppModeManager, SafeDeskMode


def test_phase_16_launch_to_admin_to_lock_to_launch_flow():
    manager = AppModeManager(SafeDeskMode.LAUNCH)

    assert manager.transition_to(SafeDeskMode.ADMIN_GATE).success is True
    assert manager.current_mode == SafeDeskMode.ADMIN_GATE

    assert manager.transition_to(SafeDeskMode.ADMIN_CONSOLE).success is True
    assert manager.current_mode == SafeDeskMode.ADMIN_CONSOLE

    assert manager.transition_to(SafeDeskMode.PUBLIC_LOCK).success is True
    assert manager.current_mode == SafeDeskMode.PUBLIC_LOCK

    assert manager.transition_to(SafeDeskMode.LAUNCH).success is True
    assert manager.current_mode == SafeDeskMode.LAUNCH


def test_phase_18_public_lock_development_return_to_admin_gate():
    manager = AppModeManager(SafeDeskMode.LAUNCH)

    manager.transition_to(SafeDeskMode.PUBLIC_LOCK)
    result = manager.transition_to(SafeDeskMode.ADMIN_GATE)

    assert result.success is True
    assert manager.current_mode == SafeDeskMode.ADMIN_GATE

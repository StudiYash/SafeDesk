from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.app_modes import AppModeManager, SafeDeskMode


def test_launch_routes_to_admin_gate_before_admin_console():
    manager = AppModeManager(SafeDeskMode.LAUNCH)

    gate = manager.transition_to(SafeDeskMode.ADMIN_GATE)
    admin = manager.transition_to(SafeDeskMode.ADMIN_CONSOLE)

    assert gate.success is True
    assert admin.success is True
    assert manager.current_mode == SafeDeskMode.ADMIN_CONSOLE


def test_launch_cannot_transition_directly_to_admin_console():
    manager = AppModeManager(SafeDeskMode.LAUNCH)

    result = manager.transition_to(SafeDeskMode.ADMIN_CONSOLE)

    assert result.success is False
    assert result.status == "blocked"
    assert manager.current_mode == SafeDeskMode.LAUNCH


def test_main_window_admin_console_route_uses_gate_method():
    source = (SRC / "safedesk" / "gui" / "main_window.py").read_text()

    assert "on_open_admin_console=self.show_admin_gate" in source
    assert "self.admin_gate_manager = AdminGateManager(self.config)" in source
    assert "self.admin_gate_manager," in source
    assert "def show_admin_gate" in source
    assert "def _open_admin_console_after_gate" in source
    assert "on_continue_setup=lambda: self._open_admin_console_after_gate(AUTHENTICATION_SETUP)" in source


def test_admin_gate_screen_uses_injected_manager_instead_of_creating_one():
    source = (SRC / "safedesk" / "gui" / "screens" / "admin_gate_screen.py").read_text()

    assert "manager: AdminGateManager" in source
    assert "self.manager = manager" in source
    assert "self.manager = AdminGateManager(" not in source
    assert "admin_gate_opened" not in source

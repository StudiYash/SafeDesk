from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _main_window_source() -> str:
    return (SRC / "safedesk" / "gui" / "main_window.py").read_text(encoding="utf-8")


def test_main_window_owns_lockdown_display_manager_and_stops_on_destroy():
    source = _main_window_source()

    assert "LockdownDisplayManager" in source
    assert "self.lockdown_display_manager = LockdownDisplayManager" in source
    assert "_stop_lockdown_display" in source
    assert "self._stop_lockdown_display()" in source


def test_show_public_lock_screen_starts_lockdown_display():
    source = _main_window_source()
    public_lock_source = source.split("def show_public_lock_screen", 1)[1].split("def show_screen", 1)[0]

    assert "self._start_lockdown_display()" in public_lock_source
    assert "PublicLockScreen" in public_lock_source
    assert "lockdown_display_already_active" in source


def test_tray_and_shortcut_still_route_to_public_lock_screen():
    source = _main_window_source()

    assert "def show_public_lock_from_tray" in source
    assert "self.show_public_lock_screen()" in source
    shortcut_source = source.split("def _handle_global_shortcut_activation", 1)[1].split("def _tray_controls_available", 1)[0]
    assert "self.show_public_lock_screen()" in shortcut_source
    assert "self.show_admin_console" not in shortcut_source


def test_returning_to_launch_or_admin_gate_cleans_up_lockdown_windows():
    source = _main_window_source()
    launch_source = source.split("def show_launch_screen", 1)[1].split("def _admin_gate_enabled", 1)[0]
    gate_source = source.split("def show_admin_gate", 1)[1].split("def show_admin_console", 1)[0]

    assert "self._stop_lockdown_display()" in launch_source
    assert "self._stop_lockdown_display()" in gate_source


def test_public_lock_screen_still_has_no_visible_admin_return_controls():
    source = (SRC / "safedesk" / "gui" / "screens" / "public_lock_screen.py").read_text(encoding="utf-8")

    assert "Return to Launch" not in source
    assert "Return to Admin Console" not in source
    assert "Developer Return" not in source

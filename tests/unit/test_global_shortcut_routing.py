from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _main_window_source() -> str:
    return (SRC / "safedesk" / "gui" / "main_window.py").read_text(encoding="utf-8")


def test_main_window_starts_and_stops_global_shortcut():
    source = _main_window_source()

    assert "_start_global_shortcut_if_configured" in source
    assert "_stop_global_shortcut" in source
    assert "WindowsHotkeyController" in source
    assert "self._stop_global_shortcut()" in source


def test_global_shortcut_activation_routes_only_to_public_lock():
    source = _main_window_source()
    handler_source = source.split("def _handle_global_shortcut_activation", 1)[1].split("def _tray_controls_available", 1)[0]

    assert "self.show_public_lock_screen()" in handler_source
    assert "self.show_admin_console" not in handler_source
    assert "self.show_admin_gate" not in handler_source
    assert "global_shortcut_public_lock_opened" in handler_source


def test_global_shortcut_activation_respects_public_lock_and_tray_flags():
    source = _main_window_source()
    handler_source = source.split("def _handle_global_shortcut_activation", 1)[1].split("def _tray_controls_available", 1)[0]

    assert "allow_when_public_lock_open" in handler_source
    assert "allow_when_minimized_to_tray" in handler_source
    assert "allow_when_admin_console_open" in handler_source
    assert "restore_from_tray()" in handler_source


def test_tray_routes_still_route_safely_after_shortcut_integration():
    source = _main_window_source()

    assert "on_open_admin_console=self.show_admin_gate_from_tray" in source
    assert "def show_admin_gate_from_tray" in source
    assert "self.show_admin_gate()" in source
    assert "def show_public_lock_from_tray" in source
    assert "self.show_public_lock_screen()" in source


def test_public_lock_screen_still_has_no_visible_admin_return_controls():
    source = (SRC / "safedesk" / "gui" / "screens" / "public_lock_screen.py").read_text(encoding="utf-8")

    assert "Return to Launch" not in source
    assert "Return to Admin Console" not in source
    assert "Developer Return" not in source


def test_global_shortcut_sources_do_not_add_persistence_hooks_or_shutdown():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (SRC / "safedesk" / "global_shortcut").glob("*.py")
    )
    forbidden = (
        "winreg",
        "schtasks",
        "Start Menu\\\\Programs\\\\Startup",
        "RunOnce",
        "Windows Service",
        "SetWindowsHookEx",
        "BlockInput",
        "pynput",
        "import keyboard",
        "shutdown /s",
        "shutdown.exe",
        "os.system(\"shutdown",
    )

    for text in forbidden:
        assert text not in combined

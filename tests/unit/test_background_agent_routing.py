from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_main_window_tray_routes_use_safe_surfaces():
    source = (SRC / "safedesk" / "gui" / "main_window.py").read_text(encoding="utf-8")

    assert "on_open_safedesk=self.show_launch_screen_from_tray" in source
    assert "on_open_admin_console=self.show_admin_gate_from_tray" in source
    assert "on_lock_safedesk=self.show_public_lock_from_tray" in source
    assert "def show_admin_gate_from_tray" in source
    assert "self.show_admin_gate()" in source
    assert "def show_public_lock_from_tray" in source
    assert "self.show_public_lock_screen()" in source
    assert "def _dispatch_gui_action_from_tray" in source
    assert "self.after(0, callback)" in source


def test_launch_screen_has_owner_controlled_tray_button():
    source = (SRC / "safedesk" / "gui" / "screens" / "launch_screen.py").read_text(encoding="utf-8")

    assert "Minimize to Tray" in source
    assert "tray_controls_enabled" in source
    assert "Tray support is unavailable." in source


def test_tray_exit_stops_controller_before_destroy():
    source = (SRC / "safedesk" / "gui" / "main_window.py").read_text(encoding="utf-8")

    assert "def exit_from_tray" in source
    assert "self.tray_controller.stop()" in source
    assert "tray_exit_requested" in source


def test_background_agent_sources_do_not_add_persistence_or_enforcement_terms():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (SRC / "safedesk" / "background_agent").glob("*.py")
    )
    forbidden = (
        "winreg",
        "schtasks",
        "Start Menu\\\\Programs\\\\Startup",
        "SetWindowsHookEx",
        "BlockInput",
        "shutdown /s",
        "shutdown.exe",
    )

    for text in forbidden:
        assert text not in combined


def test_public_lock_screen_still_has_no_visible_admin_return_controls():
    source = (SRC / "safedesk" / "gui" / "screens" / "public_lock_screen.py").read_text(encoding="utf-8")

    assert "Return to Launch" not in source
    assert "Return to Admin Console" not in source
    assert "Developer Return" not in source

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.lockdown_display.window_geometry import build_geometry


def test_fullscreen_window_source_uses_toplevel_and_public_lock_screen():
    source = (SRC / "safedesk" / "lockdown_display" / "fullscreen_window.py").read_text(encoding="utf-8")

    assert "CTkToplevel" in source
    assert "PublicLockScreen" in source
    assert "geometry(" in source
    assert "overrideredirect" in source
    assert "-topmost" in source
    assert "-fullscreen" not in source


def test_fullscreen_window_passes_per_display_size_to_public_lock_screen():
    source = (SRC / "safedesk" / "lockdown_display" / "fullscreen_window.py").read_text(encoding="utf-8")

    assert "self.lock_screen: PublicLockScreen | None = None" in source
    assert "self.lock_screen = PublicLockScreen" in source
    assert "content = PublicLockScreen" not in source
    assert "forced_width=self.display.width" in source
    assert "forced_height=self.display.height" in source
    assert "self.window.minsize(self.display.width, self.display.height)" in source
    assert "self.window.maxsize(self.display.width, self.display.height)" in source
    assert "update_idletasks" in source


def test_fullscreen_window_geometry_uses_signed_monitor_offsets():
    assert build_geometry(1920, 1080, 0, 0) == "1920x1080+0+0"
    assert build_geometry(1920, 1080, 1920, 0) == "1920x1080+1920+0"
    assert build_geometry(1920, 1080, -1920, 0) == "1920x1080-1920+0"
    assert build_geometry(1920, 1080, 0, -1080) == "1920x1080+0-1080"


def test_fullscreen_window_source_has_development_escape_without_visible_return_controls():
    source = (SRC / "safedesk" / "lockdown_display" / "fullscreen_window.py").read_text(encoding="utf-8")

    assert "allow_development_escape" in source
    assert "<Control-Shift-Q>" in source
    assert "Return to Launch" not in source
    assert "Return to Admin Console" not in source
    assert "Developer Return" not in source


def test_fullscreen_window_has_safe_visual_recovery_methods():
    source = (SRC / "safedesk" / "lockdown_display" / "fullscreen_window.py").read_text(encoding="utf-8")
    recovery_source = source.split("def recover_visual_priority", 1)[1].split("def _apply_window_attributes", 1)[0]

    assert "def is_active" in source
    assert "def recover_visual_priority" in source
    assert ".lift()" in recovery_source
    assert "attributes(\"-topmost\", True)" in recovery_source
    assert ".focus_force()" in recovery_source
    assert "update()" not in recovery_source
    assert "update_idletasks" not in recovery_source
    assert "-fullscreen" not in recovery_source


def test_lockdown_display_source_does_not_include_input_blocking_hooks_or_shutdown():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (SRC / "safedesk" / "lockdown_display").glob("*.py")
    )
    forbidden = (
        "SetWindowsHookEx",
        "BlockInput",
        "pynput",
        "import keyboard",
        "GetAsyncKeyState",
        "GetKeyState",
        "winreg",
        "schtasks",
        "Start Menu\\\\Programs\\\\Startup",
        "RunOnce",
        "Windows Service",
        "shutdown /s",
        "shutdown.exe",
        "os.system(\"shutdown",
    )

    for text in forbidden:
        assert text not in combined

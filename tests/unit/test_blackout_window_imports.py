from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_blackout_window_source_is_passive_black_toplevel_only():
    source = (SRC / "safedesk" / "lockdown_display" / "blackout_window.py").read_text(encoding="utf-8")

    assert "class BlackoutDisplayWindow" in source
    assert "CTkToplevel" in source
    assert "geometry(" in source
    assert "overrideredirect" in source
    assert "-topmost" in source
    assert "PublicLockScreen" not in source
    assert "PIL" not in source
    assert "ImageTk" not in source
    assert "Canvas" not in source
    assert "CTkButton" not in source
    assert "CTkLabel" not in source
    assert "-fullscreen" not in source
    assert "Return to Launch" not in source
    assert "Return to Admin Console" not in source
    assert "Developer Return" not in source


def test_blackout_window_has_safe_visual_recovery_without_focus_force():
    source = (SRC / "safedesk" / "lockdown_display" / "blackout_window.py").read_text(encoding="utf-8")
    recovery_source = source.split("def recover_visual_priority", 1)[1].split("def _apply_window_attributes", 1)[0]

    assert "def is_active" in source
    assert "def recover_visual_priority" in source
    assert ".lift()" in recovery_source
    assert "attributes(\"-topmost\", True)" in recovery_source
    assert "focus_force" not in recovery_source
    assert "update()" not in recovery_source
    assert "update_idletasks" not in recovery_source
    assert "-fullscreen" not in recovery_source

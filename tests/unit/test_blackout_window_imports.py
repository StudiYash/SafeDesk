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

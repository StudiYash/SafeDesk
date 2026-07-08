from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_phase_17_screen_modules_import_without_opening_window():
    import pytest

    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.launch_screen import LaunchScreen
    from safedesk.gui.screens.public_lock_screen import PublicLockScreen

    assert LaunchScreen is not None
    assert PublicLockScreen is not None


def test_public_lock_screen_public_copy_is_minimal():
    source = (SRC / "safedesk" / "gui" / "screens" / "public_lock_screen.py").read_text()

    for expected in (
        "safedesk_lockdown_template.png",
        "create_text",
        "<Button-1>",
        "<Motion>",
        "SafeDesk Lockdown",
        "Owner verification required.",
        "VERIFY OWNER",
        "RECOVERY ACCESS",
        "AWAITING OWNER VERIFICATION.",
        "OWNER VERIFICATION REQUEST RECEIVED.",
        "RECOVERY ACCESS REQUEST RECEIVED.",
        "Verify Owner",
        "Recovery Access",
    ):
        assert expected in source

    for forbidden in (
        "Return to Launch",
        "Return to Admin Console",
        "Developer Return",
        "Phase 17",
        "demo mode",
        "fullscreen",
        "keyboard",
        "mouse",
        "not available yet",
        "not implemented",
        "placeholder",
        "shutdown occurs",
    ):
        assert forbidden not in source

    assert "create_window" not in source


def test_public_lock_screen_template_asset_exists():
    assert (ROOT / "assets" / "images" / "safedesk_lockdown_template.png").exists()

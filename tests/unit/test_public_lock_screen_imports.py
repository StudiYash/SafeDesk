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


def test_public_lock_screen_uses_widget_or_forced_render_size_not_screen_size():
    source = (SRC / "safedesk" / "gui" / "screens" / "public_lock_screen.py").read_text()

    assert "winfo_screenwidth" not in source
    assert "winfo_screenheight" not in source
    assert "forced_width" in source
    assert "forced_height" in source
    assert "self.winfo_width()" in source
    assert "self.winfo_height()" in source


def test_public_lock_screen_supports_public_status_updates_without_callbacks():
    source = (SRC / "safedesk" / "gui" / "screens" / "public_lock_screen.py").read_text()

    assert "def set_status_message" in source
    assert "def _refresh_status_text_only" in source


def test_public_lock_screen_status_update_does_not_relayout_template():
    source = (SRC / "safedesk" / "gui" / "screens" / "public_lock_screen.py").read_text()
    status_source = source.split("def set_status_message", 1)[1].split("def _log_public_lock_action", 1)[0]

    assert "_refresh_status_text_only()" in status_source
    assert "_update_template_layout" not in status_source
    assert "update_idletasks" not in status_source
    assert "update()" not in status_source
    assert "template_photo_image" not in status_source
    assert "place(" not in status_source


def test_public_lock_screen_click_handlers_update_only_local_screen():
    source = (SRC / "safedesk" / "gui" / "screens" / "public_lock_screen.py").read_text()
    verify_source = source.split("def _handle_verify_owner", 1)[1].split("def _handle_recovery_access", 1)[0]
    recovery_source = source.split("def _handle_recovery_access", 1)[1].split("def set_status_message", 1)[0]

    assert "self.set_status_message(VERIFY_STATUS_TEXT)" in verify_source
    assert "self.set_status_message(RECOVERY_STATUS_TEXT)" in recovery_source
    assert "broadcast" not in verify_source
    assert "broadcast" not in recovery_source


def test_public_lock_screen_keeps_per_instance_rendered_image_references():
    source = (SRC / "safedesk" / "gui" / "screens" / "public_lock_screen.py").read_text()

    assert "self.template_rendered_image" in source
    assert "self.template_photo_image" in source
    assert "ImageTk.PhotoImage(self.template_rendered_image, master=self.winfo_toplevel())" in source
    assert "_safedesk_template_photo_image" in source


def test_public_lock_screen_template_asset_exists():
    assert (ROOT / "assets" / "images" / "safedesk_lockdown_template.png").exists()

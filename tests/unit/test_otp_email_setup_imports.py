from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import OTP_EMAIL_SETUP, SCREEN_NAMES


def test_navigation_metadata_includes_otp_email_setup():
    assert OTP_EMAIL_SETUP in SCREEN_NAMES


def test_otp_email_setup_screen_imports_without_opening_window():
    pytest.importorskip("customtkinter")

    import safedesk.gui.screens.otp_email_setup_screen

    assert safedesk.gui.screens.otp_email_setup_screen.OtpEmailSetupScreen is not None


def test_demo_otp_display_policy_without_opening_window():
    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.otp_email_setup_screen import OtpEmailSetupScreen

    generated_status = SimpleNamespace(generated=True, expired=False)
    missing_email = SimpleNamespace(
        real_email_enabled=False,
        sender_configured=False,
        app_password_present=False,
        receiver_configured=False,
    )
    ready_email = SimpleNamespace(
        real_email_enabled=True,
        sender_configured=True,
        app_password_present=True,
        receiver_configured=True,
    )
    not_generated_status = SimpleNamespace(generated=False, expired=False)

    local_text = OtpEmailSetupScreen.build_demo_otp_display_text(generated_status, missing_email, "123456")
    ready_text = OtpEmailSetupScreen.build_demo_otp_display_text(generated_status, ready_email, "123456")
    empty_text = OtpEmailSetupScreen.build_demo_otp_display_text(not_generated_status, missing_email, "123456")

    assert local_text == "Local demo OTP (foundation testing only): 123456"
    assert ready_text == "OTP generated. Real email is configured, so use Send OTP Email and check the receiver inbox."
    assert "123456" not in ready_text
    assert empty_text == "Local demo OTP: not generated"

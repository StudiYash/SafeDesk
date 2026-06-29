from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.env_loader import load_environment, parse_bool


def test_missing_env_file_does_not_fail(tmp_path):
    settings = load_environment(env_file=tmp_path / ".env", environ={})

    assert settings.env_file_loaded is False
    assert settings.safedesk_env == "development"
    assert settings.enable_real_email is False


def test_boolean_env_parsing_works():
    assert parse_bool("true") is True
    assert parse_bool("1") is True
    assert parse_bool("yes") is True
    assert parse_bool("false") is False
    assert parse_bool("0") is False
    assert parse_bool("no") is False


def test_environment_settings_sanitize_secret_presence(tmp_path):
    settings = load_environment(
        env_file=tmp_path / ".env",
        environ={
            "EMAIL_APP_PASSWORD": "private-value",
            "ENABLE_REAL_EMAIL": "true",
        },
    )

    assert settings.email_app_password_present is True
    assert not hasattr(settings, "email_app_password")
    assert settings.enable_real_email is True


def test_safedesk_prefixed_email_environment_names_work(tmp_path):
    settings = load_environment(
        env_file=tmp_path / ".env",
        environ={
            "SAFEDESK_EMAIL_SENDER_ADDRESS": "sender@example.com",
            "SAFEDESK_EMAIL_APP_PASSWORD": "private-value",
            "SAFEDESK_OTP_RECEIVER_EMAIL": "receiver@example.com",
            "SAFEDESK_ENABLE_REAL_EMAIL": "true",
        },
    )

    assert settings.email_sender_address == "sender@example.com"
    assert settings.email_app_password_present is True
    assert settings.otp_receiver_email == "receiver@example.com"
    assert settings.enable_real_email is True

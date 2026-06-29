from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.alerts.email_sender import (
    EmailSender,
    build_email_credentials_from_env,
    build_email_settings_status,
)
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.config.env_loader import load_environment
from safedesk.config.validators import build_runtime_settings, validate_config


class FakeSmtp:
    instances = []

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.logged_in = False
        self.messages = []
        FakeSmtp.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self, context=None):
        self.started_tls = True

    def login(self, sender, password):
        self.logged_in = bool(sender and password)

    def send_message(self, message):
        self.messages.append(message)


def _settings(config, env):
    report = validate_config(config, env, root=ROOT)
    return build_runtime_settings(config, env, report)


def test_email_credentials_status_reports_missing_credentials_safely():
    env = load_environment(environ={})
    settings = _settings(DEFAULT_CONFIG, env)

    status = build_email_settings_status(env, DEFAULT_CONFIG, settings)

    assert status.real_email_enabled is False
    assert status.sender_configured is False
    assert status.app_password_present is False
    assert status.receiver_configured is False


def test_email_sender_refuses_when_real_email_disabled():
    env_values = {
        "SAFEDESK_EMAIL_SENDER_ADDRESS": "sender@example.com",
        "SAFEDESK_EMAIL_APP_PASSWORD": "app-password",
        "SAFEDESK_OTP_RECEIVER_EMAIL": "receiver@example.com",
    }
    env = load_environment(environ=env_values)
    sender = EmailSender(DEFAULT_CONFIG, env, _settings(DEFAULT_CONFIG, env), environ=env_values, smtp_factory=FakeSmtp)

    result = sender.send_test_email()

    assert result.success is False
    assert result.status == "disabled"


def test_email_sender_refuses_when_credentials_missing_even_if_enabled():
    env = load_environment(environ={"SAFEDESK_ENABLE_REAL_EMAIL": "true"})
    sender = EmailSender(DEFAULT_CONFIG, env, _settings(DEFAULT_CONFIG, env), environ={}, smtp_factory=FakeSmtp)

    result = sender.send_test_email()

    assert result.success is False
    assert result.status == "missing_sender"


def test_email_sender_uses_mocked_smtp_when_enabled():
    FakeSmtp.instances = []
    env_values = {
        "SAFEDESK_ENABLE_REAL_EMAIL": "true",
        "SAFEDESK_EMAIL_SENDER_ADDRESS": "sender@example.com",
        "SAFEDESK_EMAIL_APP_PASSWORD": "app-password",
        "SAFEDESK_OTP_RECEIVER_EMAIL": "receiver@example.com",
    }
    env = load_environment(environ=env_values)
    sender = EmailSender(DEFAULT_CONFIG, env, _settings(DEFAULT_CONFIG, env), environ=env_values, smtp_factory=FakeSmtp)

    result = sender.send_otp_email("123456", 120)

    assert result.success is True
    assert FakeSmtp.instances
    instance = FakeSmtp.instances[-1]
    assert instance.host == "smtp.gmail.com"
    assert instance.port == 587
    assert instance.started_tls is True
    assert instance.logged_in is True
    assert "123456" in instance.messages[0].get_content()


def test_new_and_legacy_env_names_are_supported():
    safedesk_values = {
        "SAFEDESK_EMAIL_SENDER_ADDRESS": "sender@example.com",
        "SAFEDESK_EMAIL_APP_PASSWORD": "app-password",
        "SAFEDESK_OTP_RECEIVER_EMAIL": "receiver@example.com",
    }
    legacy_values = {
        "EMAIL_SENDER_ADDRESS": "legacy-sender@example.com",
        "EMAIL_APP_PASSWORD": "legacy-password",
        "OTP_RECEIVER_EMAIL": "legacy-receiver@example.com",
    }

    safedesk_credentials = build_email_credentials_from_env(load_environment(environ=safedesk_values), safedesk_values)
    legacy_credentials = build_email_credentials_from_env(load_environment(environ=legacy_values), legacy_values)

    assert safedesk_credentials.sender_address == "sender@example.com"
    assert safedesk_credentials.app_password_present is True
    assert legacy_credentials.sender_address == "legacy-sender@example.com"
    assert legacy_credentials.app_password_present is True

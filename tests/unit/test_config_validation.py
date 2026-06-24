from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.config.env_loader import load_environment
from safedesk.config.validators import validate_config


def _env(values=None):
    return load_environment(environ=values or {})


def test_missing_email_secrets_pass_when_real_email_disabled(tmp_path):
    report = validate_config(DEFAULT_CONFIG, _env(), root=tmp_path)

    assert report.is_valid is True
    assert not any(issue.code.startswith("missing_email") for issue in report.issues)


def test_missing_email_secrets_fail_when_real_email_enabled(tmp_path):
    env = _env({"ENABLE_REAL_EMAIL": "true"})

    report = validate_config(DEFAULT_CONFIG, env, root=tmp_path)

    assert report.is_valid is False
    assert {issue.code for issue in report.errors} >= {
        "missing_email_sender",
        "missing_email_secret",
        "missing_otp_receiver",
    }


def test_demo_mode_conflicts_with_real_shutdown_and_lockdown(tmp_path):
    config = deep_merge(
        DEFAULT_CONFIG,
        {
            "feature_flags": {
                "enable_real_shutdown": True,
                "enable_real_lockdown": True,
            }
        },
    )

    report = validate_config(config, _env(), root=tmp_path)

    assert report.is_valid is False
    assert "demo_real_shutdown_conflict" in {issue.code for issue in report.errors}
    assert "demo_real_lockdown_conflict" in {issue.code for issue in report.errors}


def test_secret_values_do_not_appear_in_validation_messages(tmp_path):
    env = _env(
        {
            "ENABLE_REAL_EMAIL": "true",
            "EMAIL_SENDER_ADDRESS": "owner@example.com",
            "EMAIL_APP_PASSWORD": "super-secret-app-password",
            "OTP_RECEIVER_EMAIL": "",
        }
    )

    report = validate_config(DEFAULT_CONFIG, env, root=tmp_path)
    messages = "\n".join(issue.message for issue in report.issues)

    assert "super-secret-app-password" not in messages
    assert "owner@example.com" not in messages

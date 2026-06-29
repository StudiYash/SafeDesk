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


def _report_for(overrides):
    config = deep_merge(DEFAULT_CONFIG, overrides)
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_otp_email_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)

    assert report.is_valid is True


def test_otp_demo_only_false_is_rejected():
    report = _report_for({"otp": {"demo_only": False}})

    assert report.is_valid is False
    assert "otp_demo_only_required" in {issue.code for issue in report.errors}


def test_otp_enabled_true_is_rejected_in_phase_10():
    report = _report_for({"otp": {"enabled": True}})

    assert report.is_valid is False
    assert "otp_final_auth_not_connected" in {issue.code for issue in report.errors}


def test_unsupported_otp_delivery_method_is_rejected():
    report = _report_for({"otp": {"delivery_method": "sms"}})

    assert report.is_valid is False
    assert "unsupported_otp_delivery_method" in {issue.code for issue in report.errors}


def test_boolean_numeric_otp_fields_are_rejected():
    report = _report_for({"otp": {"code_length": True}})

    assert report.is_valid is False
    assert "invalid_positive_integer" in {issue.code for issue in report.errors}


def test_negative_resend_cooldown_is_rejected():
    report = _report_for({"otp": {"resend_cooldown_seconds": -1}})

    assert report.is_valid is False
    assert "invalid_non_negative_integer" in {issue.code for issue in report.errors}


def test_email_host_must_be_non_empty():
    report = _report_for({"email": {"smtp_host": ""}})

    assert report.is_valid is False
    assert "invalid_non_empty_string" in {issue.code for issue in report.errors}


def test_email_boolean_fields_are_rejected_when_not_boolean():
    report = _report_for({"email": {"use_tls": "yes"}})

    assert report.is_valid is False
    assert "invalid_email_boolean" in {issue.code for issue in report.errors}

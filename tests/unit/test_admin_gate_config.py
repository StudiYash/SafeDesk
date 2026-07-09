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


def _report_for(admin_gate_overrides):
    config = deep_merge(DEFAULT_CONFIG, {"admin_gate": admin_gate_overrides})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_admin_gate_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)

    assert report.is_valid is True
    assert DEFAULT_CONFIG["admin_gate"]["enabled"] is True


def test_admin_gate_non_object_is_rejected():
    config = deep_merge(DEFAULT_CONFIG, {"admin_gate": "enabled"})

    report = validate_config(config, load_environment(environ={}), root=ROOT)

    assert report.is_valid is False
    assert "invalid_admin_gate_section" in {issue.code for issue in report.errors}


def test_admin_gate_non_boolean_flags_are_rejected():
    report = _report_for(
        {
            "enabled": "true",
            "foundation_enabled": 1,
            "demo_only": "yes",
            "require_password_if_configured": "true",
            "allow_development_continue_if_unconfigured": 0,
        }
    )

    assert report.is_valid is False
    assert "invalid_admin_gate_boolean" in {issue.code for issue in report.errors}


def test_admin_gate_rejects_boolean_max_attempts():
    report = _report_for({"max_attempts": True})

    assert report.is_valid is False
    assert "invalid_admin_gate_max_attempts" in {issue.code for issue in report.errors}


def test_admin_gate_rejects_max_attempts_less_than_one():
    report = _report_for({"max_attempts": 0})

    assert report.is_valid is False
    assert "invalid_admin_gate_max_attempts" in {issue.code for issue in report.errors}


def test_admin_gate_rejects_boolean_lockout_seconds():
    report = _report_for({"lockout_seconds": False})

    assert report.is_valid is False
    assert "invalid_admin_gate_lockout_seconds" in {issue.code for issue in report.errors}


def test_admin_gate_rejects_negative_lockout_seconds():
    report = _report_for({"lockout_seconds": -1})

    assert report.is_valid is False
    assert "invalid_admin_gate_lockout_seconds" in {issue.code for issue in report.errors}

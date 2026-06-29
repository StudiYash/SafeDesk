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


def _report_for(authentication_config):
    config = deep_merge(DEFAULT_CONFIG, {"authentication": authentication_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_authentication_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)

    assert report.is_valid is True


def test_authentication_demo_only_false_is_rejected():
    report = _report_for({"demo_only": False})

    assert report.is_valid is False
    assert "authentication_demo_only_required" in {issue.code for issue in report.errors}


def test_password_fallback_enabled_is_rejected_in_phase_9():
    report = _report_for({"password_fallback_enabled": True})

    assert report.is_valid is False
    assert "password_fallback_not_connected" in {issue.code for issue in report.errors}


def test_panic_code_enabled_is_rejected_in_phase_9():
    report = _report_for({"panic_code_enabled": True})

    assert report.is_valid is False
    assert "panic_code_not_connected" in {issue.code for issue in report.errors}


def test_unsupported_hash_algorithm_is_rejected():
    report = _report_for({"hash_algorithm": "argon2"})

    assert report.is_valid is False
    assert "unsupported_authentication_hash_algorithm" in {issue.code for issue in report.errors}


def test_boolean_numeric_authentication_fields_are_rejected():
    report = _report_for({"pbkdf2_iterations": True})

    assert report.is_valid is False
    assert "invalid_positive_integer" in {issue.code for issue in report.errors}


def test_absolute_secrets_path_is_rejected():
    report = _report_for({"secrets_path": str(ROOT / "secrets.local.json")})

    assert report.is_valid is False
    assert "absolute_authentication_secrets_path" in {issue.code for issue in report.errors}

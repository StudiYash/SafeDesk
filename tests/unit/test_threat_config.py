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


def _report_for(threat_config):
    config = deep_merge(DEFAULT_CONFIG, {"threat_levels": threat_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_threat_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)

    assert report.is_valid is True


def test_threat_levels_enabled_true_is_rejected():
    report = _report_for({"enabled": True})

    assert report.is_valid is False
    assert "threat_levels_enabled_must_remain_false" in {issue.code for issue in report.errors}


def test_threat_demo_only_false_is_rejected():
    report = _report_for({"demo_only": False})

    assert report.is_valid is False
    assert "threat_levels_demo_only_required" in {issue.code for issue in report.errors}


def test_absolute_threat_state_path_is_rejected():
    report = _report_for({"state_path": str(ROOT / "data" / "config" / "threat_state.json")})

    assert report.is_valid is False
    assert "absolute_relative_path" in {issue.code for issue in report.errors}


def test_boolean_threat_numeric_fields_are_rejected():
    report = _report_for(
        {
            "initial_level": True,
            "max_level": False,
            "forceful_attempt_threshold": True,
            "repeated_unknown_threshold": False,
            "failed_password_threshold": True,
            "failed_otp_threshold": False,
            "forced_exit_threshold": True,
        }
    )

    assert report.is_valid is False
    codes = {issue.code for issue in report.errors}
    assert "invalid_threat_levels_initial_level" in codes
    assert "invalid_threat_levels_max_level" in codes
    assert "invalid_positive_integer" in codes


def test_threat_max_level_other_than_five_is_rejected():
    report = _report_for({"max_level": 6})

    assert report.is_valid is False
    assert "threat_levels_max_level_required" in {issue.code for issue in report.errors}

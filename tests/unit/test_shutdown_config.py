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


def _report_for(shutdown_config, extra_config=None):
    config = deep_merge(DEFAULT_CONFIG, {"shutdown": shutdown_config})
    if extra_config:
        config = deep_merge(config, extra_config)
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_shutdown_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)

    assert report.is_valid is True


def test_real_shutdown_enabled_true_is_rejected():
    report = _report_for({"real_shutdown_enabled": True})

    assert report.is_valid is False
    assert "shutdown_feature_flag_required" in {issue.code for issue in report.errors}


def test_real_shutdown_command_enabled_true_is_rejected():
    report = _report_for({"real_shutdown_command_enabled": True})

    assert report.is_valid is False
    assert "shutdown_feature_flag_required" in {issue.code for issue in report.errors}


def test_demo_shutdown_only_false_without_full_guards_is_rejected():
    report = _report_for({"demo_shutdown_only": False})

    assert report.is_valid is False
    assert "incomplete_real_shutdown_guards" in {issue.code for issue in report.errors}


def test_absolute_shutdown_state_path_is_rejected():
    report = _report_for({"state_path": str(ROOT / "data" / "config" / "shutdown_state.json")})

    assert report.is_valid is False
    assert "absolute_relative_path" in {issue.code for issue in report.errors}


def test_shutdown_boolean_numeric_fields_are_rejected():
    report = _report_for(
        {
            "shutdown_after_threat_level": True,
            "warning_seconds": False,
            "countdown_seconds": True,
        }
    )

    assert report.is_valid is False
    error_codes = {issue.code for issue in report.errors}
    assert "invalid_shutdown_after_threat_level" in error_codes
    assert "invalid_positive_integer" in error_codes


def test_real_shutdown_countdown_below_30_is_rejected():
    report = _report_for({"real_shutdown_countdown_seconds": 10})

    assert report.is_valid is False
    assert "shutdown_real_countdown_too_short" in {issue.code for issue in report.errors}


def test_unsupported_real_shutdown_platform_is_rejected():
    report = _report_for({"real_shutdown_supported_platforms": ["Linux"]})

    assert report.is_valid is False
    assert "unsupported_shutdown_platform" in {issue.code for issue in report.errors}


def test_partial_real_shutdown_guards_are_rejected():
    report = _report_for({"allow_guarded_real_shutdown": True})

    assert report.is_valid is False
    assert "shutdown_demo_safe_mode_conflict" in {issue.code for issue in report.errors}
    assert "incomplete_real_shutdown_guards" in {issue.code for issue in report.errors}


def test_full_guarded_real_shutdown_config_can_validate_for_local_opt_in():
    report = _report_for(
        {
            "allow_guarded_real_shutdown": True,
            "real_shutdown_enabled": True,
            "real_shutdown_command_enabled": True,
            "demo_shutdown_only": False,
            "require_manual_confirmation": True,
            "real_shutdown_requires_confirmation_phrase": True,
            "real_shutdown_confirmation_phrase": "SHUT DOWN SAFEDESK TEST",
            "real_shutdown_countdown_seconds": 60,
            "allow_abort_real_shutdown": True,
        },
        {
            "feature_flags": {"enable_real_shutdown": True},
            "app": {"demo_safe_mode": False},
            "security_mode": {"default_mode": "standard"},
        },
    )

    assert report.is_valid is True


def test_shutdown_after_threat_level_must_be_zero_to_five():
    report = _report_for({"shutdown_after_threat_level": 6})

    assert report.is_valid is False
    assert "invalid_shutdown_after_threat_level" in {issue.code for issue in report.errors}

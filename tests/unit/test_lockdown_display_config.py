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


def _report_for(lockdown_display_config):
    config = deep_merge(DEFAULT_CONFIG, {"lockdown_display": lockdown_display_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_lockdown_display_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)

    assert report.is_valid is True
    assert DEFAULT_CONFIG["lockdown_display"]["fullscreen_enabled"] is True
    assert DEFAULT_CONFIG["lockdown_display"]["max_display_windows"] == 6


def test_non_object_lockdown_display_config_is_rejected():
    config = deep_merge(DEFAULT_CONFIG, {"lockdown_display": "enabled"})

    report = validate_config(config, load_environment(environ={}), root=ROOT)

    assert report.is_valid is False
    assert "invalid_lockdown_display_section" in {issue.code for issue in report.errors}


def test_lockdown_display_boolean_fields_are_rejected():
    report = _report_for(
        {
            "enabled": "yes",
            "foundation_enabled": "yes",
            "demo_only": "yes",
            "fullscreen_enabled": "yes",
            "multi_display_enabled": "yes",
            "borderless_enabled": "yes",
            "topmost_enabled": "yes",
            "primary_display_required": "yes",
            "fallback_to_primary_display": "yes",
            "allow_development_escape": "yes",
        }
    )

    assert report.is_valid is False
    assert "invalid_lockdown_display_boolean" in {issue.code for issue in report.errors}


def test_lockdown_display_demo_only_false_is_rejected():
    report = _report_for({"demo_only": False})

    assert report.is_valid is False
    assert "lockdown_display_demo_only_required" in {issue.code for issue in report.errors}


def test_lockdown_display_escape_timeout_out_of_range_is_rejected():
    too_small = _report_for({"development_escape_timeout_seconds": 4})
    too_large = _report_for({"development_escape_timeout_seconds": 301})

    assert too_small.is_valid is False
    assert too_large.is_valid is False
    assert "invalid_lockdown_display_escape_timeout" in {issue.code for issue in too_small.errors}
    assert "invalid_lockdown_display_escape_timeout" in {issue.code for issue in too_large.errors}


def test_lockdown_display_max_windows_out_of_range_is_rejected():
    too_small = _report_for({"max_display_windows": 0})
    too_large = _report_for({"max_display_windows": 9})

    assert too_small.is_valid is False
    assert too_large.is_valid is False
    assert "invalid_lockdown_display_max_windows" in {issue.code for issue in too_small.errors}
    assert "invalid_lockdown_display_max_windows" in {issue.code for issue in too_large.errors}


def test_lockdown_display_config_has_no_input_blocking_or_persistence_fields():
    display_config = DEFAULT_CONFIG["lockdown_display"]

    assert "input_blocking" not in display_config
    assert "disable_system_keys" not in display_config
    assert "startup" not in display_config
    assert "shutdown" not in display_config
    assert "alarm" not in display_config

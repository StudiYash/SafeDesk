from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.config.env_loader import load_environment
from safedesk.config.validators import validate_config


def _report_for(safe_interaction_lock_config):
    config = deep_merge(DEFAULT_CONFIG, {"safe_interaction_lock": safe_interaction_lock_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_safe_interaction_lock_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)
    example = json.loads((ROOT / "config.example.json").read_text(encoding="utf-8"))

    assert report.is_valid is True
    assert DEFAULT_CONFIG["safe_interaction_lock"]["enabled"] is True
    assert DEFAULT_CONFIG["safe_interaction_lock"]["focus_recovery_interval_seconds"] == 2
    assert example["safe_interaction_lock"]["demo_only"] is True


def test_non_object_safe_interaction_lock_config_is_rejected():
    config = deep_merge(DEFAULT_CONFIG, {"safe_interaction_lock": "enabled"})

    report = validate_config(config, load_environment(environ={}), root=ROOT)

    assert report.is_valid is False
    assert "invalid_safe_interaction_lock_section" in {issue.code for issue in report.errors}


def test_safe_interaction_lock_boolean_fields_are_rejected():
    report = _report_for(
        {
            "enabled": "yes",
            "foundation_enabled": "yes",
            "demo_only": "yes",
            "focus_recovery_enabled": "yes",
            "lift_windows_on_recovery": "yes",
            "reapply_topmost_on_recovery": "yes",
            "focus_primary_on_activation": "yes",
            "focus_primary_on_recovery": "yes",
            "cleanup_on_route_change": "yes",
            "prevent_duplicate_activation": "yes",
            "log_lifecycle_events": "yes",
        }
    )

    assert report.is_valid is False
    assert "invalid_safe_interaction_lock_boolean" in {issue.code for issue in report.errors}


def test_safe_interaction_lock_demo_only_false_is_rejected():
    report = _report_for({"demo_only": False})

    assert report.is_valid is False
    assert "safe_interaction_lock_demo_only_required" in {issue.code for issue in report.errors}


def test_safe_interaction_lock_interval_out_of_range_is_rejected():
    too_small = _report_for({"focus_recovery_interval_seconds": 0.5})
    too_large = _report_for({"focus_recovery_interval_seconds": 11})
    boolean_value = _report_for({"focus_recovery_interval_seconds": True})

    assert too_small.is_valid is False
    assert too_large.is_valid is False
    assert boolean_value.is_valid is False
    assert "invalid_safe_interaction_lock_interval" in {issue.code for issue in too_small.errors}
    assert "invalid_safe_interaction_lock_interval" in {issue.code for issue in too_large.errors}
    assert "invalid_safe_interaction_lock_interval" in {issue.code for issue in boolean_value.errors}


def test_safe_interaction_lock_config_has_no_unsafe_fields():
    lock_config = DEFAULT_CONFIG["safe_interaction_lock"]

    assert "input_blocking" not in lock_config
    assert "disable_system_keys" not in lock_config
    assert "startup" not in lock_config
    assert "shutdown" not in lock_config
    assert "alarm" not in lock_config
    assert "camera" not in lock_config

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


def _report_for(protected_config):
    config = deep_merge(DEFAULT_CONFIG, {"protected_mode": protected_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_protected_mode_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)

    assert report.is_valid is True


def test_protected_mode_enabled_true_is_rejected():
    report = _report_for({"enabled": True})

    assert report.is_valid is False
    assert "protected_mode_enabled_must_remain_false" in {issue.code for issue in report.errors}


def test_protected_mode_demo_only_false_is_rejected():
    report = _report_for({"demo_only": False})

    assert report.is_valid is False
    assert "protected_mode_demo_only_required" in {issue.code for issue in report.errors}


def test_absolute_protected_mode_state_path_is_rejected():
    report = _report_for({"state_path": str(ROOT / "data" / "config" / "protected_mode_state.json")})

    assert report.is_valid is False
    assert "absolute_relative_path" in {issue.code for issue in report.errors}


def test_protected_mode_boolean_numeric_candidate_levels_are_rejected():
    report = _report_for({"activation_candidate_threat_level": True, "shutdown_candidate_threat_level": False})

    assert report.is_valid is False
    assert "invalid_protected_mode_candidate_level" in {issue.code for issue in report.errors}


def test_protected_mode_candidate_level_order_is_rejected():
    report = _report_for({"activation_candidate_threat_level": 5, "shutdown_candidate_threat_level": 4})

    assert report.is_valid is False
    assert "protected_mode_candidate_order_invalid" in {issue.code for issue in report.errors}

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


def _report_for(recovery_codes_config):
    config = deep_merge(DEFAULT_CONFIG, {"recovery_codes": recovery_codes_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_recovery_codes_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)

    assert report.is_valid is True
    assert DEFAULT_CONFIG["recovery_codes"]["code_count"] == 5


def test_non_object_recovery_codes_config_is_rejected():
    config = deep_merge(DEFAULT_CONFIG, {"recovery_codes": "enabled"})

    report = validate_config(config, load_environment(environ={}), root=ROOT)

    assert report.is_valid is False
    assert "invalid_recovery_codes_section" in {issue.code for issue in report.errors}


def test_recovery_codes_boolean_flags_are_rejected():
    report = _report_for({"enabled": "yes", "foundation_enabled": 1, "demo_only": "true", "single_use": 0})

    assert report.is_valid is False
    assert "invalid_recovery_codes_boolean" in {issue.code for issue in report.errors}


def test_recovery_code_count_range_and_boolean_are_rejected():
    boolean_report = _report_for({"code_count": True})
    low_report = _report_for({"code_count": 0})
    high_report = _report_for({"code_count": 21})

    assert "invalid_recovery_code_count" in {issue.code for issue in boolean_report.errors}
    assert "invalid_recovery_code_count" in {issue.code for issue in low_report.errors}
    assert "invalid_recovery_code_count" in {issue.code for issue in high_report.errors}


def test_recovery_code_length_must_be_exactly_16():
    boolean_report = _report_for({"code_length": False})
    wrong_report = _report_for({"code_length": 12})

    assert "invalid_recovery_code_length" in {issue.code for issue in boolean_report.errors}
    assert "invalid_recovery_code_length" in {issue.code for issue in wrong_report.errors}


def test_recovery_special_characters_must_be_non_empty_without_whitespace():
    empty_report = _report_for({"allowed_special_characters": ""})
    whitespace_report = _report_for({"allowed_special_characters": "! @#"})

    assert "invalid_recovery_special_characters" in {issue.code for issue in empty_report.errors}
    assert "recovery_special_characters_whitespace" in {issue.code for issue in whitespace_report.errors}


def test_recovery_demo_only_false_is_rejected():
    report = _report_for({"demo_only": False})

    assert report.is_valid is False
    assert "recovery_codes_demo_only_required" in {issue.code for issue in report.errors}

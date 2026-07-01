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


def _report_for(logging_config):
    config = deep_merge(DEFAULT_CONFIG, {"logging": logging_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_logging_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)

    assert report.is_valid is True


def test_logging_demo_only_false_is_rejected():
    report = _report_for({"demo_only": False})

    assert report.is_valid is False
    assert "logging_demo_only_required" in {issue.code for issue in report.errors}


def test_absolute_logging_database_path_is_rejected():
    report = _report_for({"database_path": str(ROOT / "data" / "logs" / "safedesk.sqlite3")})

    assert report.is_valid is False
    assert "absolute_logging_database_path" in {issue.code for issue in report.errors}


def test_invalid_logging_database_extension_is_rejected():
    report = _report_for({"database_path": "data/logs/safedesk.txt"})

    assert report.is_valid is False
    assert "invalid_logging_database_extension" in {issue.code for issue in report.errors}


def test_invalid_logging_level_is_rejected():
    report = _report_for({"log_level": "TRACE"})

    assert report.is_valid is False
    assert "unsupported_logging_level" in {issue.code for issue in report.errors}


def test_boolean_logging_numeric_fields_are_rejected():
    report = _report_for({"max_recent_events": True})

    assert report.is_valid is False
    assert "invalid_positive_integer" in {issue.code for issue in report.errors}

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


def _report_for(background_agent_config):
    config = deep_merge(DEFAULT_CONFIG, {"background_agent": background_agent_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_background_agent_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)

    assert report.is_valid is True
    assert DEFAULT_CONFIG["background_agent"]["enabled"] is True
    assert DEFAULT_CONFIG["background_agent"]["close_to_tray"] is False
    assert DEFAULT_CONFIG["background_agent"]["allow_exit_from_tray"] is True


def test_non_object_background_agent_config_is_rejected():
    config = deep_merge(DEFAULT_CONFIG, {"background_agent": "enabled"})

    report = validate_config(config, load_environment(environ={}), root=ROOT)

    assert report.is_valid is False
    assert "invalid_background_agent_section" in {issue.code for issue in report.errors}


def test_background_agent_boolean_fields_are_rejected():
    report = _report_for(
        {
            "enabled": "yes",
            "foundation_enabled": "yes",
            "demo_only": "yes",
            "system_tray_enabled": "yes",
            "minimize_to_tray": "yes",
            "close_to_tray": "no",
            "allow_exit_from_tray": 1,
            "show_tray_notifications": 0,
        }
    )

    assert report.is_valid is False
    assert "invalid_background_agent_boolean" in {issue.code for issue in report.errors}


def test_background_agent_demo_only_false_is_rejected():
    report = _report_for({"demo_only": False})

    assert report.is_valid is False
    assert "background_agent_demo_only_required" in {issue.code for issue in report.errors}


def test_background_agent_notifications_true_is_rejected():
    report = _report_for({"show_tray_notifications": True})

    assert report.is_valid is False
    assert "background_agent_notifications_disabled" in {issue.code for issue in report.errors}

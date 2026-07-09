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


def _report_for(global_shortcut_config):
    config = deep_merge(DEFAULT_CONFIG, {"global_shortcut": global_shortcut_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_global_shortcut_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)

    assert report.is_valid is True
    assert DEFAULT_CONFIG["global_shortcut"]["hotkey"] == "ctrl+alt+l"
    assert DEFAULT_CONFIG["global_shortcut"]["activation_action"] == "public_lock"
    assert DEFAULT_CONFIG["global_shortcut"]["require_app_running"] is True


def test_non_object_global_shortcut_config_is_rejected():
    config = deep_merge(DEFAULT_CONFIG, {"global_shortcut": "enabled"})

    report = validate_config(config, load_environment(environ={}), root=ROOT)

    assert report.is_valid is False
    assert "invalid_global_shortcut_section" in {issue.code for issue in report.errors}


def test_global_shortcut_boolean_fields_are_rejected():
    report = _report_for(
        {
            "enabled": "yes",
            "foundation_enabled": "yes",
            "demo_only": "yes",
            "shortcut_enabled": "yes",
            "require_app_running": "yes",
            "allow_when_minimized_to_tray": "yes",
            "allow_when_admin_console_open": "yes",
            "allow_when_public_lock_open": "no",
        }
    )

    assert report.is_valid is False
    assert "invalid_global_shortcut_boolean" in {issue.code for issue in report.errors}


def test_global_shortcut_demo_only_false_is_rejected():
    report = _report_for({"demo_only": False})

    assert report.is_valid is False
    assert "global_shortcut_demo_only_required" in {issue.code for issue in report.errors}


def test_global_shortcut_require_app_running_false_is_rejected():
    report = _report_for({"require_app_running": False})

    assert report.is_valid is False
    assert "global_shortcut_require_app_running" in {issue.code for issue in report.errors}


def test_global_shortcut_unsupported_hotkey_is_rejected():
    report = _report_for({"hotkey": "ctrl+alt+a"})

    assert report.is_valid is False
    assert "unsupported_global_shortcut_hotkey" in {issue.code for issue in report.errors}


def test_global_shortcut_unsupported_action_is_rejected():
    report = _report_for({"activation_action": "admin_console"})

    assert report.is_valid is False
    assert "unsupported_global_shortcut_action" in {issue.code for issue in report.errors}


def test_global_shortcut_invalid_platforms_are_rejected():
    non_list = _report_for({"supported_platforms": "Windows"})
    unsupported = _report_for({"supported_platforms": ["Windows", "Linux"]})

    assert non_list.is_valid is False
    assert unsupported.is_valid is False
    assert "invalid_global_shortcut_platforms" in {issue.code for issue in non_list.errors}
    assert "unsupported_global_shortcut_platform" in {issue.code for issue in unsupported.errors}

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.app_modes import (
    AppModeManager,
    SafeDeskMode,
    can_open_admin_console_from_launch,
    can_open_public_lock_placeholder,
    parse_app_mode,
)
from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.config.env_loader import load_environment
from safedesk.config.validators import validate_config


def _validate_app_modes(app_modes_config):
    config = deep_merge(DEFAULT_CONFIG, {"app_modes": app_modes_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_app_modes_default_to_launch():
    manager = AppModeManager()

    assert manager.current_mode == SafeDeskMode.LAUNCH
    assert DEFAULT_CONFIG["app_modes"]["default_start_mode"] == SafeDeskMode.LAUNCH.value


def test_app_modes_valid_launch_flow_transitions():
    manager = AppModeManager()

    gate_result = manager.transition_to(SafeDeskMode.ADMIN_GATE)
    admin_result = manager.transition_to(SafeDeskMode.ADMIN_CONSOLE)
    lock_result = manager.transition_to(SafeDeskMode.PUBLIC_LOCK)
    launch_result = manager.transition_to(SafeDeskMode.LAUNCH)

    assert gate_result.success is True
    assert admin_result.success is True
    assert lock_result.success is True
    assert launch_result.success is True
    assert manager.current_mode == SafeDeskMode.LAUNCH


def test_app_modes_public_lock_can_return_to_admin_gate_for_development():
    manager = AppModeManager(SafeDeskMode.PUBLIC_LOCK)

    result = manager.transition_to("admin_gate")

    assert result.success is True
    assert result.previous_mode == SafeDeskMode.PUBLIC_LOCK
    assert result.new_mode == SafeDeskMode.ADMIN_GATE


def test_app_modes_invalid_transition_is_blocked():
    manager = AppModeManager(SafeDeskMode.BACKGROUND_AGENT)

    result = manager.transition_to(SafeDeskMode.PUBLIC_LOCK)

    assert result.success is False
    assert result.status == "blocked"
    assert manager.current_mode == SafeDeskMode.BACKGROUND_AGENT


def test_app_modes_parse_unsupported_value_safely():
    assert parse_app_mode("unsupported") is None


def test_app_modes_default_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)

    assert report.is_valid is True


def test_app_modes_reject_unsupported_default_start_mode():
    report = _validate_app_modes({"default_start_mode": "background_agent"})

    assert report.is_valid is False
    assert "unsupported_app_default_start_mode" in {issue.code for issue in report.errors}


def test_app_modes_reject_non_object_section():
    config = deep_merge(DEFAULT_CONFIG, {"app_modes": "launch"})

    report = validate_config(config, load_environment(environ={}), root=ROOT)

    assert report.is_valid is False
    assert "invalid_app_modes_section" in {issue.code for issue in report.errors}


def test_app_modes_reject_non_boolean_route_flags():
    report = _validate_app_modes(
        {
            "allow_public_lock_placeholder": "yes",
            "allow_admin_console_from_launch": 1,
        }
    )

    assert report.is_valid is False
    assert "invalid_app_modes_boolean" in {issue.code for issue in report.errors}


def test_app_modes_route_flags_default_to_enabled():
    assert can_open_admin_console_from_launch(DEFAULT_CONFIG) is True
    assert can_open_public_lock_placeholder(DEFAULT_CONFIG) is True


def test_app_modes_route_flags_can_disable_launch_routes():
    config = deep_merge(
        DEFAULT_CONFIG,
        {
            "app_modes": {
                "allow_admin_console_from_launch": False,
                "allow_public_lock_placeholder": False,
            }
        },
    )

    assert can_open_admin_console_from_launch(config) is False
    assert can_open_public_lock_placeholder(config) is False

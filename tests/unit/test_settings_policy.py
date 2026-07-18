from dataclasses import replace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.settings import MANAGED_SETTING_PATHS, SettingsPolicy, managed_snapshot_from_config


EXPECTED_PATHS = {
    ("ui", "start_maximized"),
    ("background_agent", "minimize_to_tray"),
    ("background_agent", "close_to_tray"),
    ("background_agent", "allow_exit_from_tray"),
    ("global_shortcut", "shortcut_enabled"),
    ("logging", "max_recent_events"),
    ("logging", "retention_days"),
    ("alarm", "manual_preview_enabled"),
    ("alarm", "max_preview_duration_seconds"),
    ("alarm", "beep_fallback_enabled"),
    ("alarm", "volume"),
    ("developer_tools", "show_demo_screens"),
    ("developer_tools", "show_runtime_diagnostics"),
}


def test_managed_settings_whitelist_is_exact_and_excludes_sensitive_controls():
    assert set(MANAGED_SETTING_PATHS.values()) == EXPECTED_PATHS
    serialized = repr(MANAGED_SETTING_PATHS).lower()
    for forbidden in ("password", "secret", "admin_gate", "shutdown", "camera", "recognition", "otp", "email", "path"):
        assert forbidden not in serialized


def test_valid_snapshot_builds_only_whitelisted_patch():
    snapshot = managed_snapshot_from_config(DEFAULT_CONFIG)
    policy = SettingsPolicy()
    patch = policy.build_patch(snapshot)

    assert policy.validate(snapshot).success
    assert {(section, key) for section, values in patch.items() for key in values} == EXPECTED_PATHS


def test_boolean_numeric_and_cross_field_validation():
    snapshot = managed_snapshot_from_config(DEFAULT_CONFIG)
    policy = SettingsPolicy()

    assert not policy.validate(replace(snapshot, start_maximized=1)).success
    for value in (9, 501, True):
        assert not policy.validate(replace(snapshot, max_recent_events=value)).success
    for value in (0, 3651, True):
        assert not policy.validate(replace(snapshot, retention_days=value)).success
    for value in (0, 11, True):
        assert not policy.validate(replace(snapshot, alarm_preview_duration_seconds=value)).success
    for value in (-0.1, 1.1, True):
        assert not policy.validate(replace(snapshot, alarm_advisory_volume=value)).success
    assert not policy.validate(replace(snapshot, minimize_to_tray=False, close_to_tray=True)).success

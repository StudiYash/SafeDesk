"""Whitelist and validation policy for owner-managed SafeDesk settings."""

from __future__ import annotations

from types import MappingProxyType

from safedesk.settings.settings_models import ManagedSettingsSnapshot, SettingsValidationResult

MANAGED_SETTING_PATHS = MappingProxyType(
    {
        "start_maximized": ("ui", "start_maximized"),
        "minimize_to_tray": ("background_agent", "minimize_to_tray"),
        "close_to_tray": ("background_agent", "close_to_tray"),
        "allow_exit_from_tray": ("background_agent", "allow_exit_from_tray"),
        "global_shortcut_enabled": ("global_shortcut", "shortcut_enabled"),
        "max_recent_events": ("logging", "max_recent_events"),
        "retention_days": ("logging", "retention_days"),
        "manual_alarm_preview_enabled": ("alarm", "manual_preview_enabled"),
        "alarm_preview_duration_seconds": ("alarm", "max_preview_duration_seconds"),
        "alarm_beep_fallback_enabled": ("alarm", "beep_fallback_enabled"),
        "alarm_advisory_volume": ("alarm", "volume"),
        "show_demo_screens": ("developer_tools", "show_demo_screens"),
        "show_runtime_diagnostics": ("developer_tools", "show_runtime_diagnostics"),
    }
)

BOOLEAN_SETTING_FIELDS = (
    "start_maximized",
    "minimize_to_tray",
    "close_to_tray",
    "allow_exit_from_tray",
    "global_shortcut_enabled",
    "manual_alarm_preview_enabled",
    "alarm_beep_fallback_enabled",
    "show_demo_screens",
    "show_runtime_diagnostics",
)


def managed_snapshot_from_config(config: dict) -> ManagedSettingsSnapshot:
    """Build a typed snapshot from effective startup configuration."""

    def value(section: str, key: str, default):
        raw_section = config.get(section, {}) if isinstance(config, dict) else {}
        return raw_section.get(key, default) if isinstance(raw_section, dict) else default

    return ManagedSettingsSnapshot(
        start_maximized=value("ui", "start_maximized", False),
        minimize_to_tray=value("background_agent", "minimize_to_tray", True),
        close_to_tray=value("background_agent", "close_to_tray", False),
        allow_exit_from_tray=value("background_agent", "allow_exit_from_tray", True),
        global_shortcut_enabled=value("global_shortcut", "shortcut_enabled", True),
        max_recent_events=value("logging", "max_recent_events", 50),
        retention_days=value("logging", "retention_days", 30),
        manual_alarm_preview_enabled=value("alarm", "manual_preview_enabled", True),
        alarm_preview_duration_seconds=value("alarm", "max_preview_duration_seconds", 5),
        alarm_beep_fallback_enabled=value("alarm", "beep_fallback_enabled", True),
        alarm_advisory_volume=value("alarm", "volume", 0.5),
        show_demo_screens=value("developer_tools", "show_demo_screens", True),
        show_runtime_diagnostics=value("developer_tools", "show_runtime_diagnostics", True),
    )


class SettingsPolicy:
    """Validate typed settings and produce only the approved nested patch."""

    def validate(self, snapshot: ManagedSettingsSnapshot) -> SettingsValidationResult:
        if not isinstance(snapshot, ManagedSettingsSnapshot):
            return SettingsValidationResult(False, "invalid_settings", "Settings input is unavailable.")

        for field_name in BOOLEAN_SETTING_FIELDS:
            if not isinstance(getattr(snapshot, field_name), bool):
                return SettingsValidationResult(False, "invalid_boolean", "A settings toggle has an invalid value.")

        issue = self._integer_range(snapshot.max_recent_events, 10, 500, "Maximum recent events")
        if issue:
            return issue
        issue = self._integer_range(snapshot.retention_days, 1, 3650, "Retention days")
        if issue:
            return issue
        issue = self._integer_range(snapshot.alarm_preview_duration_seconds, 1, 10, "Alarm preview duration")
        if issue:
            return issue

        volume = snapshot.alarm_advisory_volume
        if isinstance(volume, bool) or not isinstance(volume, (int, float)) or not 0.0 <= float(volume) <= 1.0:
            return SettingsValidationResult(False, "invalid_alarm_volume", "Alarm advisory volume must be between 0.0 and 1.0.")

        if snapshot.close_to_tray and not snapshot.minimize_to_tray:
            return SettingsValidationResult(
                False,
                "invalid_tray_combination",
                "Close to tray requires Minimize to tray to remain enabled.",
            )
        return SettingsValidationResult(True, "valid", "Managed settings are valid.")

    def build_patch(self, snapshot: ManagedSettingsSnapshot) -> dict:
        validation = self.validate(snapshot)
        if not validation.success:
            return {}
        patch: dict = {}
        for field_name, (section, key) in MANAGED_SETTING_PATHS.items():
            patch.setdefault(section, {})[key] = getattr(snapshot, field_name)
        return patch

    @staticmethod
    def changed_count(before: ManagedSettingsSnapshot, after: ManagedSettingsSnapshot) -> int:
        return sum(getattr(before, field) != getattr(after, field) for field in MANAGED_SETTING_PATHS)

    @staticmethod
    def _integer_range(value, minimum: int, maximum: int, label: str) -> SettingsValidationResult | None:
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            return SettingsValidationResult(
                False,
                "invalid_integer_range",
                f"{label} must be an integer between {minimum} and {maximum}.",
            )
        return None

"""Typed models for approved SafeDesk owner settings."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ManagedSettingsSnapshot:
    start_maximized: bool
    minimize_to_tray: bool
    close_to_tray: bool
    allow_exit_from_tray: bool
    global_shortcut_enabled: bool
    max_recent_events: int
    retention_days: int
    manual_alarm_preview_enabled: bool
    alarm_preview_duration_seconds: int
    alarm_beep_fallback_enabled: bool
    alarm_advisory_volume: float
    show_demo_screens: bool
    show_runtime_diagnostics: bool


@dataclass(frozen=True)
class SettingsValidationResult:
    success: bool
    status: str
    message: str


@dataclass(frozen=True)
class SettingsOperationResult:
    success: bool
    status: str
    message: str
    changed_setting_count: int
    restart_required: bool
    local_override_present: bool


@dataclass(frozen=True)
class SettingsStatus:
    local_override_present: bool
    configuration_valid: bool
    managed_setting_count: int
    restart_required: bool
    message: str

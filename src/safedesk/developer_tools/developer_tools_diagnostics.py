"""Privacy-safe diagnostics for the guarded Developer Tools page."""

from __future__ import annotations

from safedesk.alarm import WindowsAudioPreviewBackend
from safedesk.developer_tools.developer_tools_models import (
    DeveloperDiagnostic,
    DeveloperDiagnosticsSummary,
)
from safedesk.developer_tools.developer_tools_policy import DeveloperToolsPolicy


class DeveloperToolsDiagnostics:
    def __init__(
        self,
        config: dict,
        *,
        effective_environment: str | None = None,
        configuration_valid: bool = True,
        alarm_backend=None,
    ):
        self.config = config if isinstance(config, dict) else {}
        self.effective_environment = effective_environment
        self.configuration_valid = configuration_valid is True
        self.alarm_backend = alarm_backend or WindowsAudioPreviewBackend()

    def build_summary(self) -> DeveloperDiagnosticsSummary:
        status = DeveloperToolsPolicy(
            self.config,
            effective_environment=self.effective_environment,
        ).build_status()
        if not status.diagnostics_visible:
            return DeveloperDiagnosticsSummary((), "Runtime diagnostics are hidden by policy.")

        items = (
            DeveloperDiagnostic("Environment", "development" if status.environment_supported else "unsupported"),
            DeveloperDiagnostic("Demo-safe mode", self._enabled(status.demo_safe_mode)),
            DeveloperDiagnostic("Security mode", "demo_safe" if status.security_mode_supported else "other"),
            DeveloperDiagnostic("Configuration validation", "valid" if self.configuration_valid else "invalid"),
            DeveloperDiagnostic("Developer Tools foundation", self._enabled(status.foundation_enabled)),
            DeveloperDiagnostic("Demo routes", "available" if status.demo_routes_allowed else "hidden"),
            DeveloperDiagnostic("Runtime diagnostics", "enabled"),
            DeveloperDiagnostic("Logging foundation", self._foundation("logging", "enabled")),
            DeveloperDiagnostic("Alarm backend", "available" if self._alarm_available() else "unavailable"),
            DeveloperDiagnostic("Tray foundation", self._foundation("background_agent", "foundation_enabled")),
            DeveloperDiagnostic("Global shortcut foundation", self._foundation("global_shortcut", "foundation_enabled")),
            DeveloperDiagnostic("Lockdown display foundation", self._foundation("lockdown_display", "foundation_enabled")),
            DeveloperDiagnostic("Safe interaction lock", self._foundation("safe_interaction_lock", "foundation_enabled")),
        )
        return DeveloperDiagnosticsSummary(items, "Safe runtime diagnostics are available.")

    def _foundation(self, section: str, key: str) -> str:
        value = self.config.get(section, {})
        return self._enabled(isinstance(value, dict) and value.get(key) is True)

    def _alarm_available(self) -> bool:
        try:
            return self.alarm_backend.is_available() is True
        except Exception:
            return False

    @staticmethod
    def _enabled(value: bool) -> str:
        return "enabled" if value else "disabled"

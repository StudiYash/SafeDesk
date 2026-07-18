"""Owner-facing service for typed SafeDesk managed settings."""

from __future__ import annotations

from pathlib import Path

from safedesk.config.models import EnvironmentSettings
from safedesk.settings.local_settings_store import LocalSettingsStore
from safedesk.settings.settings_models import (
    ManagedSettingsSnapshot,
    SettingsOperationResult,
    SettingsStatus,
)
from safedesk.settings.settings_policy import MANAGED_SETTING_PATHS, managed_snapshot_from_config


class SettingsService:
    def __init__(
        self,
        config: dict,
        env: EnvironmentSettings,
        *,
        configuration_valid: bool = True,
        root: Path | None = None,
        store: LocalSettingsStore | None = None,
    ):
        self.config = config if isinstance(config, dict) else {}
        self.configuration_valid = configuration_valid is True
        self.store = store or LocalSettingsStore(env, root=root)

    def current_snapshot(self) -> ManagedSettingsSnapshot:
        return managed_snapshot_from_config(self.config)

    def save(self, snapshot: ManagedSettingsSnapshot) -> SettingsOperationResult:
        return self.store.save(snapshot)

    def restore_defaults(self) -> SettingsOperationResult:
        return self.store.restore_defaults()

    def build_status(self) -> SettingsStatus:
        local_present = self.store.local_override_present()
        message = "Local managed settings are loaded." if local_present else "SafeDesk is using public/default settings."
        return SettingsStatus(
            local_override_present=local_present,
            configuration_valid=self.configuration_valid,
            managed_setting_count=len(MANAGED_SETTING_PATHS),
            restart_required=False,
            message=message,
        )

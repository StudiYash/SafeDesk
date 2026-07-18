"""Atomic ignored-local persistence for approved SafeDesk settings."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

from safedesk.config.config_loader import deep_merge, load_config
from safedesk.config.models import EnvironmentSettings
from safedesk.config.validators import validate_config
from safedesk.settings.settings_models import ManagedSettingsSnapshot, SettingsOperationResult
from safedesk.settings.settings_policy import (
    MANAGED_SETTING_PATHS,
    SettingsPolicy,
    managed_snapshot_from_config,
)
from safedesk.storage.paths import local_config_path, project_root


class LocalSettingsStore:
    """Persist one whitelisted patch to the fixed ignored local config file."""

    def __init__(
        self,
        env: EnvironmentSettings,
        *,
        root: Path | None = None,
        replace_func: Callable[[str | Path, str | Path], None] = os.replace,
    ):
        self.root = (root or project_root()).resolve()
        self.local_path = local_config_path(self.root)
        self.temp_path = self.local_path.with_name(f"{self.local_path.name}.tmp")
        self.env = env
        self.replace_func = replace_func
        self.policy = SettingsPolicy()

    def save(self, snapshot: ManagedSettingsSnapshot) -> SettingsOperationResult:
        validation = self.policy.validate(snapshot)
        if not validation.success:
            return self._result(False, validation.status, validation.message, 0, False)

        local_data = self._read_local_data()
        if local_data is None:
            return self._result(
                False,
                "local_config_invalid",
                "Local settings could not be read safely.",
                0,
                self.local_path.is_file(),
            )

        base_config = self._load_base_config()
        if base_config is None:
            return self._result(False, "base_config_unavailable", "Settings could not be validated safely.", 0, self.local_path.is_file())

        persisted_config = deep_merge(base_config, local_data)
        persisted_snapshot = managed_snapshot_from_config(persisted_config)
        changed_count = self.policy.changed_count(persisted_snapshot, snapshot)
        if changed_count == 0:
            return self._result(True, "no_changes", "No managed settings changed.", 0, self.local_path.is_file(), restart=False)

        candidate_local = deep_merge(local_data, self.policy.build_patch(snapshot))
        if not self._candidate_valid(base_config, candidate_local):
            return self._result(
                False,
                "validation_failed",
                "Managed settings were rejected by safe configuration validation.",
                0,
                self.local_path.is_file(),
            )
        write_status = self._write_atomic(candidate_local)
        if write_status != "verified":
            status = "verification_failed" if write_status == "verification_failed" else "write_failed"
            return self._result(
                False,
                status,
                "Managed settings persistence could not be verified safely.",
                0,
                self.local_path.is_file(),
            )
        return self._result(
            True,
            "saved",
            "Settings saved locally and verified. Restart SafeDesk to apply them.",
            changed_count,
            True,
        )

    def restore_defaults(self) -> SettingsOperationResult:
        local_data = self._read_local_data()
        if local_data is None:
            return self._result(
                False,
                "local_config_invalid",
                "Local settings could not be read safely.",
                0,
                self.local_path.is_file(),
            )

        candidate_local = json.loads(json.dumps(local_data))
        changed_count = 0
        for section, key in MANAGED_SETTING_PATHS.values():
            section_data = candidate_local.get(section)
            if not isinstance(section_data, dict) or key not in section_data:
                continue
            del section_data[key]
            changed_count += 1
            if not section_data:
                del candidate_local[section]

        if changed_count == 0:
            return self._result(
                True,
                "no_changes",
                "Managed settings already use safe defaults.",
                0,
                self.local_path.is_file(),
                restart=False,
            )

        base_config = self._load_base_config()
        if base_config is None or not self._candidate_valid(base_config, candidate_local):
            return self._result(False, "validation_failed", "Safe defaults could not be validated.", 0, self.local_path.is_file())
        write_status = self._write_atomic(candidate_local)
        if write_status != "verified":
            status = "verification_failed" if write_status == "verification_failed" else "write_failed"
            return self._result(
                False,
                status,
                "Safe-default persistence could not be verified safely.",
                0,
                self.local_path.is_file(),
            )
        return self._result(
            True,
            "defaults_restored",
            "Managed settings were restored. Restart SafeDesk to apply these changes.",
            changed_count,
            True,
        )

    def local_override_present(self) -> bool:
        return self.local_path.is_file()

    def _read_local_data(self) -> dict | None:
        if not self.local_path.exists():
            return {}
        try:
            with self.local_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    def _load_base_config(self) -> dict | None:
        try:
            return load_config(root=self.root, include_local=False).config
        except Exception:
            return None

    def _candidate_valid(self, base_config: dict, local_data: dict) -> bool:
        try:
            candidate = deep_merge(base_config, local_data)
            return validate_config(candidate, self.env, root=self.root).is_valid
        except Exception:
            return False

    def _write_atomic(self, data: dict) -> str:
        try:
            with self.temp_path.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(data, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            self.replace_func(self.temp_path, self.local_path)
            if not self._verify_persisted_data(data):
                return "verification_failed"
            return "verified"
        except Exception:
            try:
                if self.temp_path.exists():
                    self.temp_path.unlink()
            except Exception:
                pass
            return "write_failed"

    def _verify_persisted_data(self, expected: dict) -> bool:
        try:
            with self.local_path.open("r", encoding="utf-8") as handle:
                persisted = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return False
        return isinstance(persisted, dict) and persisted == expected

    def _result(
        self,
        success: bool,
        status: str,
        message: str,
        changed_count: int,
        local_present: bool,
        *,
        restart: bool | None = None,
    ) -> SettingsOperationResult:
        restart_required = changed_count > 0 if restart is None else restart
        return SettingsOperationResult(
            success=success,
            status=status,
            message=message,
            changed_setting_count=changed_count,
            restart_required=restart_required,
            local_override_present=local_present,
        )

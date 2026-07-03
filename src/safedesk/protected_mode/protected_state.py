"""Ignored local protected-mode state loading and storage."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from safedesk.protected_mode.protected_models import PROTECTED_MODE_STATES, ProtectedModeState
from safedesk.storage.paths import project_root

STATE_VERSION = 1


def utc_timestamp() -> str:
    """Return a UTC timestamp for local state metadata."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_protected_mode_state_path(config: dict) -> Path:
    """Resolve the ignored protected-mode state path relative to project root."""

    raw_path = config.get("protected_mode", config).get("state_path", "data/config/protected_mode_state.json")
    path = Path(str(raw_path))
    return path if path.is_absolute() else project_root() / path


def default_protected_mode_state(demo_only: bool = True) -> ProtectedModeState:
    """Return the safe inactive default protected-mode state."""

    return ProtectedModeState(updated_at=utc_timestamp(), demo_only=bool(demo_only))


def protected_mode_state_to_dict(state: ProtectedModeState) -> dict[str, Any]:
    """Convert protected-mode state to public-safe JSON data."""

    return {
        "version": STATE_VERSION,
        "protected_mode_state": {
            "mode": str(state.mode),
            "armed": bool(state.armed),
            "active_demo": bool(state.active_demo),
            "recovery_required": bool(state.recovery_required),
            "last_action": str(state.last_action),
            "last_reason": str(state.last_reason),
            "updated_at": str(state.updated_at),
            "demo_only": bool(state.demo_only),
            "threat_level_at_last_update": int(state.threat_level_at_last_update),
            "shutdown_candidate": bool(state.shutdown_candidate),
            "lockdown_performed": False,
            "shutdown_performed": False,
        },
    }


def protected_mode_state_from_dict(data: dict[str, Any], demo_only: bool = True) -> ProtectedModeState:
    """Build protected-mode state from JSON, falling back safely on malformed values."""

    if not isinstance(data, dict):
        return default_protected_mode_state(demo_only)
    raw_state = data.get("protected_mode_state", data)
    if not isinstance(raw_state, dict):
        return default_protected_mode_state(demo_only)

    mode = raw_state.get("mode", "inactive")
    safe_mode = mode if isinstance(mode, str) and mode in PROTECTED_MODE_STATES else "inactive"

    def safe_bool(key: str, default: bool = False) -> bool:
        value = raw_state.get(key, default)
        return value if isinstance(value, bool) else default

    def safe_level(key: str) -> int:
        value = raw_state.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, int):
            return 0
        return max(0, min(5, value))

    def safe_text(key: str, default: str) -> str:
        value = raw_state.get(key, default)
        return str(value)[:300] if isinstance(value, str) else default

    updated_at = raw_state.get("updated_at", "")
    return ProtectedModeState(
        mode=safe_mode,
        armed=safe_bool("armed"),
        active_demo=safe_bool("active_demo"),
        recovery_required=safe_bool("recovery_required"),
        last_action=safe_text("last_action", "loaded"),
        last_reason=safe_text("last_reason", "Protected mode foundation state loaded."),
        updated_at=str(updated_at)[:80] if isinstance(updated_at, str) and updated_at else utc_timestamp(),
        demo_only=safe_bool("demo_only", demo_only),
        threat_level_at_last_update=safe_level("threat_level_at_last_update"),
        shutdown_candidate=safe_bool("shutdown_candidate"),
        lockdown_performed=False,
        shutdown_performed=False,
    )


def load_protected_mode_state(path: Path, demo_only: bool = True) -> ProtectedModeState:
    """Load ignored local protected-mode state, returning inactive default if missing or corrupt."""

    if not path.exists():
        return default_protected_mode_state(demo_only)
    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
    except Exception:
        return default_protected_mode_state(demo_only)
    return protected_mode_state_from_dict(loaded, demo_only)


def save_protected_mode_state(path: Path, state: ProtectedModeState) -> None:
    """Write ignored local protected-mode state using a temporary file then replace."""

    path.parent.mkdir(parents=True, exist_ok=True)
    state_to_save = state if state.updated_at else replace(state, updated_at=utc_timestamp())
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(protected_mode_state_to_dict(state_to_save), handle, indent=2, sort_keys=True)
        handle.write("\n")
    temp_path.replace(path)

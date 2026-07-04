"""Ignored local shutdown escalation state loading and storage."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from safedesk.shutdown_escalation.shutdown_models import SHUTDOWN_ESCALATION_STATES, ShutdownEscalationState
from safedesk.storage.paths import project_root

STATE_VERSION = 1


def utc_timestamp() -> str:
    """Return a UTC timestamp for local state metadata."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_shutdown_state_path(config: dict) -> Path:
    """Resolve the ignored shutdown escalation state path relative to project root."""

    raw_path = config.get("shutdown", config).get("state_path", "data/config/shutdown_state.json")
    path = Path(str(raw_path))
    return path if path.is_absolute() else project_root() / path


def default_shutdown_state(demo_only: bool = True, manual_confirmation_required: bool = True) -> ShutdownEscalationState:
    """Return the safe idle default shutdown escalation state."""

    return ShutdownEscalationState(
        updated_at=utc_timestamp(),
        demo_only=bool(demo_only),
        manual_confirmation_required=bool(manual_confirmation_required),
    )


def shutdown_state_to_dict(state: ShutdownEscalationState) -> dict[str, Any]:
    """Convert shutdown escalation state to public-safe JSON data."""

    return {
        "version": STATE_VERSION,
        "shutdown_escalation_state": {
            "mode": str(state.mode),
            "shutdown_candidate": bool(state.shutdown_candidate),
            "countdown_running": bool(state.countdown_running),
            "countdown_remaining_seconds": int(state.countdown_remaining_seconds),
            "countdown_total_seconds": int(state.countdown_total_seconds),
            "last_action": str(state.last_action),
            "last_reason": str(state.last_reason),
            "updated_at": str(state.updated_at),
            "demo_only": bool(state.demo_only),
            "threat_level_at_last_update": int(state.threat_level_at_last_update),
            "protected_mode_at_last_update": str(state.protected_mode_at_last_update),
            "protected_shutdown_candidate": bool(state.protected_shutdown_candidate),
            "manual_confirmation_required": bool(state.manual_confirmation_required),
            "real_shutdown_enabled": bool(state.real_shutdown_enabled),
            "real_shutdown_command_enabled": bool(state.real_shutdown_command_enabled),
            "guarded_real_shutdown_ready": bool(state.guarded_real_shutdown_ready),
            "real_shutdown_confirmation_matched": bool(state.real_shutdown_confirmation_matched),
            "real_shutdown_requested": bool(state.real_shutdown_requested),
            "real_shutdown_scheduled": bool(state.real_shutdown_scheduled),
            "real_shutdown_abort_requested": bool(state.real_shutdown_abort_requested),
            "real_shutdown_aborted": bool(state.real_shutdown_aborted),
            "real_shutdown_countdown_seconds": int(state.real_shutdown_countdown_seconds),
            "real_shutdown_platform": str(state.real_shutdown_platform),
            "real_shutdown_result_status": str(state.real_shutdown_result_status),
            "real_shutdown_result_message": str(state.real_shutdown_result_message),
            "shutdown_performed": False,
            "restart_performed": False,
            "logoff_performed": False,
            "lockdown_performed": False,
            "alarm_performed": False,
            "email_sent": False,
        },
    }


def shutdown_state_from_dict(
    data: dict[str, Any],
    demo_only: bool = True,
    manual_confirmation_required: bool = True,
) -> ShutdownEscalationState:
    """Build shutdown escalation state from JSON, falling back safely on malformed values."""

    if not isinstance(data, dict):
        return default_shutdown_state(demo_only, manual_confirmation_required)
    raw_state = data.get("shutdown_escalation_state", data)
    if not isinstance(raw_state, dict):
        return default_shutdown_state(demo_only, manual_confirmation_required)

    mode = raw_state.get("mode", "idle")
    safe_mode = mode if isinstance(mode, str) and mode in SHUTDOWN_ESCALATION_STATES else "idle"

    def safe_bool(key: str, default: bool = False) -> bool:
        value = raw_state.get(key, default)
        return value if isinstance(value, bool) else default

    def safe_seconds(key: str) -> int:
        value = raw_state.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, int):
            return 0
        return max(0, min(3600, value))

    def safe_level(key: str) -> int:
        value = raw_state.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, int):
            return 0
        return max(0, min(5, value))

    def safe_text(key: str, default: str) -> str:
        value = raw_state.get(key, default)
        return str(value)[:300] if isinstance(value, str) else default

    updated_at = raw_state.get("updated_at", "")
    return ShutdownEscalationState(
        mode=safe_mode,
        shutdown_candidate=safe_bool("shutdown_candidate"),
        countdown_running=safe_bool("countdown_running"),
        countdown_remaining_seconds=safe_seconds("countdown_remaining_seconds"),
        countdown_total_seconds=safe_seconds("countdown_total_seconds"),
        last_action=safe_text("last_action", "loaded"),
        last_reason=safe_text("last_reason", "Shutdown escalation dry-run state loaded."),
        updated_at=str(updated_at)[:80] if isinstance(updated_at, str) and updated_at else utc_timestamp(),
        demo_only=safe_bool("demo_only", demo_only),
        threat_level_at_last_update=safe_level("threat_level_at_last_update"),
        protected_mode_at_last_update=safe_text("protected_mode_at_last_update", "inactive"),
        protected_shutdown_candidate=safe_bool("protected_shutdown_candidate"),
        manual_confirmation_required=safe_bool("manual_confirmation_required", manual_confirmation_required),
        real_shutdown_enabled=safe_bool("real_shutdown_enabled"),
        real_shutdown_command_enabled=safe_bool("real_shutdown_command_enabled"),
        guarded_real_shutdown_ready=safe_bool("guarded_real_shutdown_ready"),
        real_shutdown_confirmation_matched=safe_bool("real_shutdown_confirmation_matched"),
        real_shutdown_requested=safe_bool("real_shutdown_requested"),
        real_shutdown_scheduled=safe_bool("real_shutdown_scheduled"),
        real_shutdown_abort_requested=safe_bool("real_shutdown_abort_requested"),
        real_shutdown_aborted=safe_bool("real_shutdown_aborted"),
        real_shutdown_countdown_seconds=safe_seconds("real_shutdown_countdown_seconds"),
        real_shutdown_platform=safe_text("real_shutdown_platform", ""),
        real_shutdown_result_status=safe_text("real_shutdown_result_status", "not_requested"),
        real_shutdown_result_message=safe_text("real_shutdown_result_message", "Guarded real shutdown state loaded."),
        shutdown_performed=False,
        restart_performed=False,
        logoff_performed=False,
        lockdown_performed=False,
        alarm_performed=False,
        email_sent=False,
    )


def load_shutdown_state(
    path: Path,
    demo_only: bool = True,
    manual_confirmation_required: bool = True,
) -> ShutdownEscalationState:
    """Load ignored local shutdown state, returning idle default if missing or corrupt."""

    if not path.exists():
        return default_shutdown_state(demo_only, manual_confirmation_required)
    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
    except Exception:
        return default_shutdown_state(demo_only, manual_confirmation_required)
    return shutdown_state_from_dict(loaded, demo_only, manual_confirmation_required)


def save_shutdown_state(path: Path, state: ShutdownEscalationState) -> None:
    """Write ignored local shutdown state using a temporary file then replace."""

    path.parent.mkdir(parents=True, exist_ok=True)
    state_to_save = state if state.updated_at else replace(state, updated_at=utc_timestamp())
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(shutdown_state_to_dict(state_to_save), handle, indent=2, sort_keys=True)
        handle.write("\n")
    temp_path.replace(path)

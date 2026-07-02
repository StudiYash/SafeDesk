"""Ignored local threat state loading and storage."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from safedesk.storage.paths import project_root
from safedesk.threats.threat_models import ThreatState

STATE_VERSION = 1


def utc_timestamp() -> str:
    """Return a UTC timestamp for local state metadata."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_threat_state_path(config: dict) -> Path:
    """Resolve the ignored threat state path relative to the project root."""

    raw_path = config.get("threat_levels", config).get("state_path", "data/config/threat_state.json")
    path = Path(str(raw_path))
    return path if path.is_absolute() else project_root() / path


def default_threat_state(initial_level: int = 0, demo_only: bool = True) -> ThreatState:
    """Return a safe default state."""

    safe_level = max(0, min(5, int(initial_level)))
    return ThreatState(
        current_level=safe_level,
        highest_level=safe_level,
        last_reason="Safe idle." if safe_level == 0 else f"Initialized at Level {safe_level}.",
        updated_at=utc_timestamp(),
        demo_only=bool(demo_only),
    )


def threat_state_to_dict(state: ThreatState) -> dict[str, Any]:
    """Convert a threat state to public-safe JSON data."""

    return {
        "version": STATE_VERSION,
        "threat_state": {
            "current_level": int(state.current_level),
            "highest_level": int(state.highest_level),
            "unknown_unverified_count": int(state.unknown_unverified_count),
            "failed_password_count": int(state.failed_password_count),
            "failed_otp_count": int(state.failed_otp_count),
            "failed_panic_count": int(state.failed_panic_count),
            "forced_exit_count": int(state.forced_exit_count),
            "last_reason": str(state.last_reason),
            "updated_at": str(state.updated_at),
            "demo_only": bool(state.demo_only),
        },
    }


def threat_state_from_dict(data: dict[str, Any], initial_level: int = 0, demo_only: bool = True) -> ThreatState:
    """Build a threat state from JSON data, falling back safely on malformed values."""

    if not isinstance(data, dict):
        return default_threat_state(initial_level, demo_only)
    raw_state = data.get("threat_state", data)
    if not isinstance(raw_state, dict):
        return default_threat_state(initial_level, demo_only)

    def safe_int(key: str, default: int = 0) -> int:
        value = raw_state.get(key, default)
        if isinstance(value, bool) or not isinstance(value, int):
            return default
        return max(0, min(5 if key.endswith("level") else 1_000_000, value))

    current_level = safe_int("current_level", initial_level)
    highest_level = max(current_level, safe_int("highest_level", current_level))
    last_reason = raw_state.get("last_reason", "Safe idle.")
    updated_at = raw_state.get("updated_at", "")

    return ThreatState(
        current_level=current_level,
        highest_level=highest_level,
        unknown_unverified_count=safe_int("unknown_unverified_count"),
        failed_password_count=safe_int("failed_password_count"),
        failed_otp_count=safe_int("failed_otp_count"),
        failed_panic_count=safe_int("failed_panic_count"),
        forced_exit_count=safe_int("forced_exit_count"),
        last_reason=str(last_reason)[:300] if isinstance(last_reason, str) else "Safe idle.",
        updated_at=str(updated_at)[:80] if isinstance(updated_at, str) and updated_at else utc_timestamp(),
        demo_only=bool(raw_state.get("demo_only", demo_only)),
    )


def load_threat_state(path: Path, initial_level: int = 0, demo_only: bool = True) -> ThreatState:
    """Load ignored local threat state, returning default state if missing or corrupt."""

    if not path.exists():
        return default_threat_state(initial_level, demo_only)
    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
    except Exception:
        return default_threat_state(initial_level, demo_only)
    return threat_state_from_dict(loaded, initial_level, demo_only)


def save_threat_state(path: Path, state: ThreatState) -> None:
    """Write ignored local threat state using a temporary file then replace."""

    path.parent.mkdir(parents=True, exist_ok=True)
    state_to_save = state if state.updated_at else replace(state, updated_at=utc_timestamp())
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(threat_state_to_dict(state_to_save), handle, indent=2, sort_keys=True)
        handle.write("\n")
    temp_path.replace(path)

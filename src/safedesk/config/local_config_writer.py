"""Safe local setup configuration writer."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from safedesk.config.config_loader import deep_merge
from safedesk.config.exceptions import SafeDeskConfigFileError, SafeDeskValidationError
from safedesk.storage.paths import local_config_path
from safedesk.utils.constants import DEFAULT_SECURITY_MODE, SUPPORTED_SECURITY_MODES
from safedesk.config.validators import is_basic_email

FORBIDDEN_SETUP_KEYS = {
    "password",
    "password_hash",
    "otp",
    "otp_secret",
    "panic_code",
    "recovery_code",
    "secret",
    "token",
    "credential",
    "face_image",
    "face_encoding",
    "face_encoding_path",
    "owner_image_path",
}


@dataclass(frozen=True)
class LocalSetupPayload:
    owner_name: str
    owner_email: str = ""
    preferred_security_mode: str = DEFAULT_SECURITY_MODE
    demo_safe_mode: bool = True
    camera_index: int = 0
    privacy_acknowledged: bool = False
    safe_mode_acknowledged: bool = False


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _load_existing(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SafeDeskConfigFileError(f"Invalid JSON in {path.name}: {exc.msg}") from exc
    except OSError as exc:
        raise SafeDeskConfigFileError(f"Unable to read {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise SafeDeskConfigFileError(f"{path.name} must contain a JSON object.")
    return data


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower()
            if any(forbidden in normalized for forbidden in FORBIDDEN_SETUP_KEYS):
                return True
            if _contains_forbidden_key(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _validate_payload(payload: LocalSetupPayload) -> None:
    if not payload.owner_name.strip():
        raise SafeDeskValidationError("Owner display name is required to complete setup.")
    if payload.owner_email.strip():
        if payload.owner_email.strip() and not is_basic_email(payload.owner_email.strip()):
            raise SafeDeskValidationError("Owner email must use a basic email format when provided.")
    if payload.preferred_security_mode not in SUPPORTED_SECURITY_MODES:
        raise SafeDeskValidationError("Preferred security mode is not supported.")
    if isinstance(payload.camera_index, bool) or not isinstance(payload.camera_index, int) or payload.camera_index < 0:
        raise SafeDeskValidationError("Camera index must be zero or a positive integer placeholder.")
    if not payload.privacy_acknowledged:
        raise SafeDeskValidationError("Privacy acknowledgement is required.")
    if not payload.safe_mode_acknowledged:
        raise SafeDeskValidationError("Safe/demo mode acknowledgement is required.")


def build_safe_local_config(payload: LocalSetupPayload, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    _validate_payload(payload)
    if existing is not None and _contains_forbidden_key(existing):
        raise SafeDeskValidationError("Existing local config contains unsupported sensitive setup fields.")

    current = deepcopy(existing or {})
    now = _utc_now()
    completed_at = current.get("setup", {}).get("completed_at") or now
    setup_update = {
        "setup": {
            "completed": True,
            "setup_version": 1,
            "completed_at": completed_at,
            "last_updated_at": now,
        },
        "owner_profile": {
            "owner_name": payload.owner_name.strip(),
            "owner_email": payload.owner_email.strip(),
        },
        "security_mode": {
            "default_mode": payload.preferred_security_mode,
        },
        "app": {
            "demo_safe_mode": True,
        },
        "setup_preferences": {
            "camera_index": payload.camera_index,
            "privacy_acknowledged": payload.privacy_acknowledged,
            "safe_mode_acknowledged": payload.safe_mode_acknowledged,
        },
    }
    return deep_merge(current, setup_update)


def save_local_setup_config(
    payload: LocalSetupPayload,
    path: Path | None = None,
) -> Path:
    target = path or local_config_path()
    existing = _load_existing(target)
    config = build_safe_local_config(payload, existing=existing)

    if _contains_forbidden_key(config):
        raise SafeDeskValidationError("Refusing to write unsupported sensitive setup fields.")

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")
    return target

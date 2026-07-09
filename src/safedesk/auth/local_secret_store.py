"""Ignored local storage for SafeDesk authentication hash records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from safedesk.auth.password_hashing import PasswordHashRecord, password_record_from_dict, password_record_to_dict
from safedesk.storage.paths import project_root

SECRET_STORE_VERSION = 1


@dataclass(frozen=True)
class StoredSecretRecord:
    """Hash record plus local metadata."""

    record: PasswordHashRecord
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class StoredRecoveryCodeRecord:
    """Single-use hashed owner recovery code record."""

    code_id: str
    record: PasswordHashRecord
    created_at: str
    used_at: str = ""
    used: bool = False


@dataclass(frozen=True)
class AuthenticationSecretStoreData:
    """Parsed local authentication secret store data."""

    version: int = SECRET_STORE_VERSION
    master_password: StoredSecretRecord | None = None
    panic_code: StoredSecretRecord | None = None
    recovery_codes: tuple[StoredRecoveryCodeRecord, ...] = ()
    store_present: bool = False
    load_error: str = ""


@dataclass(frozen=True)
class AuthenticationSecretStatus:
    """Safe status summary for GUI and setup pages."""

    store_present: bool
    readable: bool
    master_password_configured: bool
    panic_code_configured: bool
    recovery_codes_configured: bool
    recovery_code_count: int
    unused_recovery_code_count: int
    used_recovery_code_count: int
    message: str


@dataclass(frozen=True)
class LocalSecretStoreResult:
    """Status-style result for local store operations."""

    success: bool
    message: str
    data: AuthenticationSecretStoreData | None = None


def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_secrets_path(config: dict[str, Any]) -> Path:
    """Resolve the configured local secrets path without creating it."""

    authentication = config.get("authentication", config)
    raw_path = authentication.get("secrets_path", "secrets.local.json")
    path = Path(str(raw_path))
    return path if path.is_absolute() else project_root() / path


def _stored_record_from_dict(data: dict[str, Any] | None) -> StoredSecretRecord | None:
    if not isinstance(data, dict):
        return None

    record = password_record_from_dict(data)
    created_at = data.get("created_at", "")
    updated_at = data.get("updated_at", "")
    return StoredSecretRecord(
        record=record,
        created_at=created_at if isinstance(created_at, str) else "",
        updated_at=updated_at if isinstance(updated_at, str) else "",
    )


def _stored_record_to_dict(stored: StoredSecretRecord) -> dict[str, Any]:
    data = password_record_to_dict(stored.record)
    data["created_at"] = stored.created_at
    data["updated_at"] = stored.updated_at
    return data


def _recovery_code_from_dict(data: dict[str, Any] | None) -> StoredRecoveryCodeRecord | None:
    if not isinstance(data, dict):
        return None

    record_data = data.get("record")
    if not isinstance(record_data, dict):
        record_data = data

    record = password_record_from_dict(record_data)
    code_id = data.get("id", "")
    created_at = data.get("created_at", "")
    used_at = data.get("used_at", "")
    used = data.get("used", False)
    return StoredRecoveryCodeRecord(
        code_id=code_id if isinstance(code_id, str) else "",
        record=record,
        created_at=created_at if isinstance(created_at, str) else "",
        used_at=used_at if isinstance(used_at, str) else "",
        used=used is True,
    )


def _recovery_code_to_dict(stored: StoredRecoveryCodeRecord) -> dict[str, Any]:
    return {
        "id": stored.code_id,
        "record": password_record_to_dict(stored.record),
        "created_at": stored.created_at,
        "used_at": stored.used_at,
        "used": stored.used,
    }


def _recovery_codes_from_list(data: Any) -> tuple[StoredRecoveryCodeRecord, ...]:
    if not isinstance(data, list):
        return ()
    records: list[StoredRecoveryCodeRecord] = []
    for item in data:
        try:
            record = _recovery_code_from_dict(item)
        except Exception:
            record = None
        if record is not None:
            records.append(record)
    return tuple(records)


def load_authentication_secrets(path: Path) -> AuthenticationSecretStoreData:
    """Load local authentication secrets, treating missing storage as unconfigured."""

    if not path.exists():
        return AuthenticationSecretStoreData(store_present=False)

    try:
        raw_data = json.loads(path.read_text(encoding="utf-8"))
        authentication = raw_data.get("authentication", {})
        return AuthenticationSecretStoreData(
            version=int(raw_data.get("version", SECRET_STORE_VERSION)),
            master_password=_stored_record_from_dict(authentication.get("master_password")),
            panic_code=_stored_record_from_dict(authentication.get("panic_code")),
            recovery_codes=_recovery_codes_from_list(authentication.get("recovery_codes")),
            store_present=True,
        )
    except Exception:
        return AuthenticationSecretStoreData(
            store_present=True,
            load_error="Local authentication secret store could not be read.",
        )


def save_authentication_secrets(path: Path, data: AuthenticationSecretStoreData) -> None:
    """Write local authentication secrets using a temporary file then replace."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"version": SECRET_STORE_VERSION, "authentication": {}}
    if data.master_password is not None:
        payload["authentication"]["master_password"] = _stored_record_to_dict(data.master_password)
    if data.panic_code is not None:
        payload["authentication"]["panic_code"] = _stored_record_to_dict(data.panic_code)
    if data.recovery_codes:
        payload["authentication"]["recovery_codes"] = [_recovery_code_to_dict(record) for record in data.recovery_codes]

    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


def build_authentication_secret_status(path: Path) -> AuthenticationSecretStatus:
    """Return a safe summary of the local authentication secret store."""

    data = load_authentication_secrets(path)
    if data.load_error:
        return AuthenticationSecretStatus(
            store_present=data.store_present,
            readable=False,
            master_password_configured=False,
            panic_code_configured=False,
            recovery_codes_configured=False,
            recovery_code_count=0,
            unused_recovery_code_count=0,
            used_recovery_code_count=0,
            message=data.load_error,
        )

    master_configured = data.master_password is not None
    panic_configured = data.panic_code is not None
    recovery_code_count = len(data.recovery_codes)
    used_recovery_code_count = sum(1 for record in data.recovery_codes if record.used)
    unused_recovery_code_count = recovery_code_count - used_recovery_code_count
    if not data.store_present:
        message = "Local authentication secrets are not configured."
    elif master_configured or panic_configured or recovery_code_count:
        message = "Local authentication secret store is readable."
    else:
        message = "Local authentication secret store is present but empty."

    return AuthenticationSecretStatus(
        store_present=data.store_present,
        readable=True,
        master_password_configured=master_configured,
        panic_code_configured=panic_configured,
        recovery_codes_configured=recovery_code_count > 0,
        recovery_code_count=recovery_code_count,
        unused_recovery_code_count=unused_recovery_code_count,
        used_recovery_code_count=used_recovery_code_count,
        message=message,
    )


class LocalSecretStore:
    """Small object wrapper around the local authentication secret store."""

    def __init__(self, path: Path):
        self.path = path

    def load(self) -> AuthenticationSecretStoreData:
        return load_authentication_secrets(self.path)

    def save(self, data: AuthenticationSecretStoreData) -> None:
        save_authentication_secrets(self.path, data)

    def status(self) -> AuthenticationSecretStatus:
        return build_authentication_secret_status(self.path)

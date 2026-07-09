"""Safe event logging service for SafeDesk foundation flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from safedesk.logging.log_models import (
    EVENT_CATEGORIES,
    EVENT_SEVERITIES,
    EVENT_STATUSES,
    EventLogResult,
    SafeDeskEvent,
)
from safedesk.logging.sqlite_log_store import SQLiteLogStore
from safedesk.storage.paths import project_root

SENSITIVE_METADATA_WORDS = (
    "password",
    "panic",
    "otp",
    "code",
    "token",
    "secret",
    "credential",
    "app_password",
    "hash",
    "salt",
    "email_body",
    "body",
    "embedding",
    "image",
    "face",
    "path",
)
SAFE_METADATA_KEYS = {
    "failed_otp_count",
    "failed_panic_count",
    "failed_password_count",
    "image_saved",
    "image_count",
    "password_configured",
    "recovery_codes_configured",
    "recovery_code_count",
    "unused_recovery_code_count",
    "used_recovery_code_count",
}

MAX_STRING_LENGTH = 300
MAX_DICT_ITEMS = 50
MAX_LIST_ITEMS = 20


def resolve_log_database_path(config: dict) -> Path:
    """Resolve the configured logging database path relative to project root."""

    raw_path = config.get("logging", config).get("database_path", "data/logs/safedesk.sqlite3")
    path = Path(str(raw_path))
    return path if path.is_absolute() else project_root() / path


def sanitize_metadata(metadata: dict | None) -> dict:
    """Return metadata safe for SQLite storage and dashboard display."""

    if not isinstance(metadata, dict):
        return {}
    return _sanitize_dict(metadata)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    if normalized in SAFE_METADATA_KEYS:
        return False
    return any(word in normalized for word in SENSITIVE_METADATA_WORDS)


def _truncate(value: str) -> str:
    if len(value) <= MAX_STRING_LENGTH:
        return value
    return f"{value[:MAX_STRING_LENGTH]}..."


def _sanitize_dict(data: dict) -> dict:
    sanitized: dict[str, Any] = {}
    for index, (key, value) in enumerate(data.items()):
        if index >= MAX_DICT_ITEMS:
            sanitized["truncated"] = True
            break
        safe_key = _truncate(str(key))
        if _is_sensitive_key(safe_key):
            sanitized[safe_key] = "[REDACTED]"
        else:
            sanitized[safe_key] = _sanitize_value(value)
    return sanitized


def _sanitize_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _truncate(value)
    if isinstance(value, dict):
        return _sanitize_dict(value)
    if isinstance(value, (list, tuple, set)):
        return [_sanitize_value(item) for item in list(value)[:MAX_LIST_ITEMS]]
    return _truncate(str(value))


class EventLogger:
    """Safe facade for writing local foundation events."""

    def __init__(self, config: dict, store: SQLiteLogStore | None = None):
        self.config = config
        self.logging_config = config.get("logging", {})
        self.store = store or SQLiteLogStore(resolve_log_database_path(config))

    @property
    def enabled(self) -> bool:
        return self.logging_config.get("enabled", True) is True

    def log_event(
        self,
        category: str,
        action: str,
        status: str,
        severity: str = "INFO",
        message: str = "",
        metadata: dict | None = None,
        source: str = "gui",
        session_id: str = "local",
    ) -> EventLogResult:
        """Write a sanitized event if local logging is enabled."""

        if not self.enabled:
            return EventLogResult(False, "skipped", "Event logging is disabled.")

        safe_category = category if category in EVENT_CATEGORIES else "system"
        safe_status = status if status in EVENT_STATUSES else "info"
        safe_severity = severity if severity in EVENT_SEVERITIES else "INFO"
        event = SafeDeskEvent(
            category=safe_category,
            action=_truncate(str(action or "unspecified")),
            status=safe_status,
            severity=safe_severity,
            message=_truncate(str(message or "")),
            metadata=sanitize_metadata(metadata),
            source=_truncate(str(source or "gui")),
            session_id=_truncate(str(session_id or "local")),
        )

        try:
            return self.store.add_event(event)
        except Exception:
            return EventLogResult(False, "storage_error", "Event could not be written to local SQLite logs.")

    def log_app_event(self, action: str, status: str = "info", message: str = "", metadata: dict | None = None) -> EventLogResult:
        return self.log_event("app", action, status, "INFO", message, metadata)

    def log_auth_event(self, action: str, status: str, message: str = "", metadata: dict | None = None) -> EventLogResult:
        severity = "WARNING" if status in {"failed", "blocked"} else "INFO"
        return self.log_event("authentication", action, status, severity, message, metadata)

    def log_otp_event(self, action: str, status: str, message: str = "", metadata: dict | None = None) -> EventLogResult:
        severity = "WARNING" if status in {"failed", "blocked"} else "INFO"
        return self.log_event("otp", action, status, severity, message, metadata)


def build_logger_from_config(config: dict) -> EventLogger:
    """Build a logger from the current runtime config."""

    return EventLogger(config)

"""Safe event log models for the local SQLite logging foundation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

EVENT_CATEGORIES = (
    "app",
    "setup",
    "owner_registration",
    "recognition_demo",
    "liveness_demo",
    "authentication",
    "otp",
    "email",
    "intruder_detection",
    "threat_level",
    "protected_mode",
    "system",
)

EVENT_STATUSES = ("success", "failed", "blocked", "skipped", "info")
EVENT_SEVERITIES = ("DEBUG", "INFO", "WARNING", "ERROR")


def utc_timestamp() -> str:
    """Return a UTC timestamp suitable for SQLite text storage."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class SafeDeskEvent:
    """A sanitized SafeDesk event record."""

    category: str
    action: str
    status: str
    severity: str = "INFO"
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = "gui"
    session_id: str = "local"
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=utc_timestamp)
    event_number: int = 0


@dataclass(frozen=True)
class EventLogResult:
    """Result of an event logging operation."""

    success: bool
    status: str
    message: str
    event_id: str = ""
    deleted_count: int = 0


@dataclass(frozen=True)
class EventLogStatus:
    """Safe status summary for the local event database."""

    enabled: bool
    database_ready: bool
    event_count: int
    message: str


@dataclass(frozen=True)
class EventLogSummary:
    """Recent-event summary safe for dashboard display."""

    status: EventLogStatus
    recent_events: tuple[SafeDeskEvent, ...] = ()

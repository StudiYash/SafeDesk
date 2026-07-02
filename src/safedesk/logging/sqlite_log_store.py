"""SQLite-backed local event store for SafeDesk foundation logs."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

from safedesk.logging.log_models import EventLogResult, EventLogStatus, SafeDeskEvent


class SQLiteLogStore:
    """Create and manage the local SafeDesk event log database."""

    def __init__(self, database_path: Path):
        self.database_path = database_path

    def initialize(self) -> EventLogResult:
        """Create the SQLite database schema if needed."""

        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.database_path) as connection:
                if self._events_table_exists(connection) and "event_number" not in self._table_columns(connection):
                    self._migrate_legacy_events_table(connection)
                self._create_schema(connection)
                connection.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
                connection.execute("CREATE INDEX IF NOT EXISTS idx_events_category ON events(category)")
                connection.execute("CREATE INDEX IF NOT EXISTS idx_events_severity ON events(severity)")
                connection.execute("CREATE INDEX IF NOT EXISTS idx_events_event_number ON events(event_number)")
        except Exception:
            return EventLogResult(False, "storage_error", "Local event log database could not be initialized.")

        return EventLogResult(True, "ready", "Local event log database is ready.")

    def add_event(self, event: SafeDeskEvent) -> EventLogResult:
        """Insert a sanitized event."""

        init_result = self.initialize()
        if not init_result.success:
            return init_result

        try:
            with sqlite3.connect(self.database_path) as connection:
                connection.execute(
                    """
                    INSERT INTO events (
                        event_id,
                        timestamp,
                        category,
                        action,
                        status,
                        severity,
                        message,
                        metadata_json,
                        source,
                        session_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_id,
                        event.timestamp,
                        event.category,
                        event.action,
                        event.status,
                        event.severity,
                        event.message,
                        json.dumps(event.metadata, sort_keys=True),
                        event.source,
                        event.session_id,
                    ),
                )
        except Exception:
            return EventLogResult(False, "storage_error", "Event could not be written to local SQLite logs.")

        return EventLogResult(True, "logged", "Event written to local SQLite logs.", event_id=event.event_id)

    def list_events(self, limit: int | None = None) -> list[SafeDeskEvent]:
        """Return events in stable insertion order."""

        if not self.database_path.exists():
            return []

        try:
            with sqlite3.connect(self.database_path) as connection:
                if "event_number" not in self._table_columns(connection):
                    return []
                if limit is None:
                    rows = connection.execute(
                        """
                        SELECT event_number, event_id, timestamp, category, action, status, severity, message, metadata_json, source, session_id
                        FROM events
                        ORDER BY event_number ASC
                        """
                    ).fetchall()
                else:
                    rows = connection.execute(
                        """
                        SELECT event_number, event_id, timestamp, category, action, status, severity, message, metadata_json, source, session_id
                        FROM events
                        ORDER BY event_number ASC
                        LIMIT ?
                        """,
                        (max(1, int(limit)),),
                    ).fetchall()
        except Exception:
            return []

        return [self._event_from_row(row) for row in rows]

    def list_recent_events(self, limit: int) -> list[SafeDeskEvent]:
        """Return recent events newest first."""

        if not self.database_path.exists():
            return []

        safe_limit = max(1, int(limit))
        try:
            with sqlite3.connect(self.database_path) as connection:
                if "event_number" not in self._table_columns(connection):
                    return []
                rows = connection.execute(
                    """
                    SELECT event_number, event_id, timestamp, category, action, status, severity, message, metadata_json, source, session_id
                    FROM events
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()
        except Exception:
            return []

        return [self._event_from_row(row) for row in rows]

    def count_events(self) -> int:
        """Return the number of stored events."""

        if not self.database_path.exists():
            return 0
        try:
            with sqlite3.connect(self.database_path) as connection:
                return int(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0])
        except Exception:
            return 0

    def build_status(self, enabled: bool = True) -> EventLogStatus:
        """Return safe status for the database without exposing private paths."""

        if not enabled:
            return EventLogStatus(False, False, 0, "Event logging is disabled.")

        if not self.database_path.exists():
            return EventLogStatus(True, False, 0, "Local event log database has not been created yet.")

        init_result = self.initialize()
        if not init_result.success:
            return EventLogStatus(True, False, 0, init_result.message)

        return EventLogStatus(True, True, self.count_events(), "Local event log database is ready.")

    def clear_events(self) -> EventLogResult:
        """Clear only local SafeDesk event rows and reset event numbering."""

        if not self.database_path.exists():
            return EventLogResult(True, "cleared", "No local event logs were present.", deleted_count=0)

        try:
            with sqlite3.connect(self.database_path) as connection:
                if not self._events_table_exists(connection):
                    return EventLogResult(True, "cleared", "No local event records were present.", deleted_count=0)
                deleted_count = int(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0])
                connection.execute("DELETE FROM events")
                if self._events_table_exists(connection) and "sqlite_sequence" in self._sqlite_master_tables(connection):
                    connection.execute("DELETE FROM sqlite_sequence WHERE name = ?", ("events",))
                connection.commit()
                connection.execute("VACUUM")
        except Exception:
            return EventLogResult(False, "storage_error", "Local event logs could not be cleared.")

        return EventLogResult(True, "cleared", "Local event logs cleared.", deleted_count=deleted_count)

    def clear_events_for_demo(self) -> EventLogResult:
        """Backward-compatible wrapper for clearing local demo event logs."""

        return self.clear_events()

    @staticmethod
    def _event_from_row(row: tuple[Any, ...]) -> SafeDeskEvent:
        metadata: dict[str, Any]
        try:
            loaded = json.loads(row[8])
            metadata = loaded if isinstance(loaded, dict) else {}
        except Exception:
            metadata = {}

        return SafeDeskEvent(
            event_number=int(row[0] or 0),
            event_id=str(row[1]),
            timestamp=str(row[2]),
            category=str(row[3]),
            action=str(row[4]),
            status=str(row[5]),
            severity=str(row[6]),
            message=str(row[7]),
            metadata=metadata,
            source=str(row[9]),
            session_id=str(row[10]),
        )

    @staticmethod
    def _events_table_exists(connection: sqlite3.Connection) -> bool:
        row = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'").fetchone()
        return row is not None

    @staticmethod
    def _table_columns(connection: sqlite3.Connection) -> set[str]:
        return {str(row[1]) for row in connection.execute("PRAGMA table_info(events)").fetchall()}

    @staticmethod
    def _sqlite_master_tables(connection: sqlite3.Connection) -> set[str]:
        rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        return {str(row[0]) for row in rows}

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_number INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                source TEXT NOT NULL,
                session_id TEXT NOT NULL
            )
            """
        )

    def _migrate_legacy_events_table(self, connection: sqlite3.Connection) -> None:
        connection.execute("DROP INDEX IF EXISTS idx_events_timestamp")
        connection.execute("DROP INDEX IF EXISTS idx_events_category")
        connection.execute("DROP INDEX IF EXISTS idx_events_severity")
        connection.execute("DROP INDEX IF EXISTS idx_events_event_number")
        connection.execute("ALTER TABLE events RENAME TO events_legacy")
        self._create_schema(connection)
        connection.execute(
            """
            INSERT INTO events (
                event_id,
                timestamp,
                category,
                action,
                status,
                severity,
                message,
                metadata_json,
                source,
                session_id
            )
            SELECT
                event_id,
                timestamp,
                category,
                action,
                status,
                severity,
                message,
                metadata_json,
                source,
                session_id
            FROM events_legacy
            ORDER BY timestamp ASC, event_id ASC
            """
        )
        connection.execute("DROP TABLE events_legacy")

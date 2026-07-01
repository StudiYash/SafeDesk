from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.logging.log_models import SafeDeskEvent
from safedesk.logging.sqlite_log_store import SQLiteLogStore


def test_sqlite_store_initializes_database_and_table(tmp_path):
    db_path = tmp_path / "logs" / "safedesk.sqlite3"
    store = SQLiteLogStore(db_path)

    result = store.initialize()

    assert result.success is True
    assert db_path.exists()
    with sqlite3.connect(db_path) as connection:
        table = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'").fetchone()
        columns = {row[1] for row in connection.execute("PRAGMA table_info(events)").fetchall()}
    assert table is not None
    assert "event_number" in columns


def test_sqlite_store_adds_event_counts_and_assigns_event_number(tmp_path):
    store = SQLiteLogStore(tmp_path / "safedesk.sqlite3")
    event = SafeDeskEvent(category="app", action="manual_test", status="info", message="Test event")

    result = store.add_event(event)

    assert result.success is True
    assert store.count_events() == 1
    [stored] = store.list_events()
    assert stored.event_number == 1


def test_sqlite_store_returns_default_events_by_stable_event_number(tmp_path):
    store = SQLiteLogStore(tmp_path / "safedesk.sqlite3")
    older = SafeDeskEvent(category="app", action="older", status="info", timestamp="2026-06-29T10:00:00+00:00")
    newer = SafeDeskEvent(category="app", action="newer", status="info", timestamp="2026-06-30T10:00:00+00:00")

    store.add_event(older)
    store.add_event(newer)
    events = store.list_events()

    assert [(event.event_number, event.action) for event in events] == [(1, "older"), (2, "newer")]


def test_sqlite_store_still_can_return_recent_events_newest_first(tmp_path):
    store = SQLiteLogStore(tmp_path / "safedesk.sqlite3")
    older = SafeDeskEvent(category="app", action="older", status="info", timestamp="2026-06-29T10:00:00+00:00")
    newer = SafeDeskEvent(category="app", action="newer", status="info", timestamp="2026-06-30T10:00:00+00:00")

    store.add_event(older)
    store.add_event(newer)
    events = store.list_recent_events(10)

    assert [(event.event_number, event.action) for event in events] == [(2, "newer"), (1, "older")]


def test_sqlite_store_round_trips_metadata(tmp_path):
    store = SQLiteLogStore(tmp_path / "safedesk.sqlite3")
    event = SafeDeskEvent(
        category="otp",
        action="otp_verification",
        status="failed",
        metadata={"attempts": 1, "result_status": "failed"},
    )

    store.add_event(event)
    [stored] = store.list_events()

    assert stored.metadata == {"attempts": 1, "result_status": "failed"}


def test_sqlite_store_status_reports_missing_without_creating_database(tmp_path):
    db_path = tmp_path / "safedesk.sqlite3"
    store = SQLiteLogStore(db_path)

    status = store.build_status(enabled=True)

    assert status.enabled is True
    assert status.database_ready is False
    assert status.event_count == 0
    assert db_path.exists() is False


def test_sqlite_store_migrates_legacy_schema_safely(tmp_path):
    db_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE events (
                event_id TEXT PRIMARY KEY,
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
        connection.execute(
            """
            INSERT INTO events (event_id, timestamp, category, action, status, severity, message, metadata_json, source, session_id)
            VALUES ('legacy-id', '2026-06-30T10:00:00+00:00', 'app', 'legacy_action', 'info', 'INFO', 'Legacy', '{}', 'gui', 'local')
            """
        )

    store = SQLiteLogStore(db_path)
    result = store.initialize()
    [event] = store.list_events()

    assert result.success is True
    assert event.event_number == 1
    assert event.event_id == "legacy-id"

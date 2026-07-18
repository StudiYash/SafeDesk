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


def test_sqlite_store_returns_bounded_newest_first_pages(tmp_path):
    store = SQLiteLogStore(tmp_path / "safedesk.sqlite3")
    for number in range(1, 121):
        store.add_event(SafeDeskEvent(category="app", action=f"event_{number}", status="info"))

    first_page = store.list_event_page(limit=50, offset=0)
    second_page = store.list_event_page(limit=50, offset=50)

    assert len(first_page) == 50
    assert len(second_page) == 50
    assert [event.event_number for event in first_page] == list(range(120, 70, -1))
    assert [event.event_number for event in second_page] == list(range(70, 20, -1))
    assert store.count_events() == 120


def test_sqlite_store_caps_page_size_and_rejects_unsafe_paging(tmp_path):
    store = SQLiteLogStore(tmp_path / "safedesk.sqlite3")
    for number in range(1, 121):
        store.add_event(SafeDeskEvent(category="app", action=f"event_{number}", status="info"))

    assert len(store.list_event_page(limit=500, offset=0)) == 100

    for limit, offset in ((0, 0), (-1, 0), (True, 0), (50, -1), (50, True)):
        try:
            store.list_event_page(limit=limit, offset=offset)
        except ValueError:
            pass
        else:
            raise AssertionError("Unsafe page values must be rejected.")


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


def test_sqlite_store_clear_events_removes_rows_and_resets_count(tmp_path):
    store = SQLiteLogStore(tmp_path / "safedesk.sqlite3")
    store.add_event(SafeDeskEvent(category="app", action="one", status="info"))
    store.add_event(SafeDeskEvent(category="app", action="two", status="info"))

    result = store.clear_events()

    assert result.success is True
    assert result.deleted_count == 2
    assert store.list_events() == []
    assert store.count_events() == 0
    assert store.build_status(enabled=True).event_count == 0
    assert "safedesk.sqlite3" not in result.message


def test_interactive_clear_path_does_not_run_vacuum():
    source = (SRC / "safedesk" / "logging" / "sqlite_log_store.py").read_text(encoding="utf-8")
    clear_body = source.split("def clear_events", 1)[1].split("def clear_events_for_demo", 1)[0]

    assert "VACUUM" not in clear_body


def test_sqlite_store_clear_events_resets_event_numbering(tmp_path):
    store = SQLiteLogStore(tmp_path / "safedesk.sqlite3")
    store.add_event(SafeDeskEvent(category="app", action="before_clear", status="info"))
    store.clear_events()

    store.add_event(SafeDeskEvent(category="app", action="after_clear", status="info"))
    [event] = store.list_events()

    assert event.event_number == 1
    assert event.action == "after_clear"


def test_sqlite_store_clear_events_missing_database_is_safe(tmp_path):
    db_path = tmp_path / "missing.sqlite3"
    store = SQLiteLogStore(db_path)

    result = store.clear_events()

    assert result.success is True
    assert result.deleted_count == 0
    assert db_path.exists() is False
    assert "missing.sqlite3" not in result.message


def test_sqlite_store_clear_events_does_not_touch_other_runtime_files(tmp_path):
    store = SQLiteLogStore(tmp_path / "logs" / "safedesk.sqlite3")
    owner_sample = tmp_path / "data" / "owner" / "samples" / "owner_sample_keep.jpg"
    intruder_image = tmp_path / "data" / "intruders" / "intruder_keep.jpg"
    threat_state = tmp_path / "data" / "config" / "threat_state.json"
    secret_file = tmp_path / "secrets.local.json"
    for path in (owner_sample, intruder_image, threat_state, secret_file):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("keep", encoding="utf-8")
    store.add_event(SafeDeskEvent(category="app", action="manual_test", status="info"))

    result = store.clear_events()

    assert result.success is True
    assert owner_sample.read_text(encoding="utf-8") == "keep"
    assert intruder_image.read_text(encoding="utf-8") == "keep"
    assert threat_state.read_text(encoding="utf-8") == "keep"
    assert secret_file.read_text(encoding="utf-8") == "keep"

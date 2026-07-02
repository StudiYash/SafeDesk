from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.logging.event_logger import EventLogger, sanitize_metadata
from safedesk.logging.sqlite_log_store import SQLiteLogStore


def _config_for(db_path: Path, enabled: bool = True) -> dict:
    return deep_merge(
        DEFAULT_CONFIG,
        {
            "logging": {
                "enabled": enabled,
                "database_path": str(db_path),
                "demo_only": True,
            }
        },
    )


def test_sanitize_metadata_redacts_sensitive_keys():
    metadata = {
        "password": "secret",
        "panic_code": "111111",
        "otp_code": "123456",
        "email_app_password": "app-secret",
        "token": "token-value",
        "hash": "hash-value",
        "salt": "salt-value",
        "image_path": "private-image.jpg",
        "image_saved": True,
        "image_count": 2,
        "face_embedding": [1, 2, 3],
        "attempts": 1,
    }

    sanitized = sanitize_metadata(metadata)

    for key in (
        "password",
        "panic_code",
        "otp_code",
        "email_app_password",
        "token",
        "hash",
        "salt",
        "image_path",
        "face_embedding",
    ):
        assert sanitized[key] == "[REDACTED]"
    assert sanitized["attempts"] == 1
    assert sanitized["image_saved"] is True
    assert sanitized["image_count"] == 2


def test_event_logger_writes_sanitized_event_to_temp_database(tmp_path):
    config = _config_for(tmp_path / "safedesk.sqlite3")
    logger = EventLogger(config)

    result = logger.log_event(
        "otp",
        "manual_verification",
        "failed",
        metadata={"otp_code": "123456", "attempts": 2},
    )

    assert result.success is True
    [event] = logger.store.list_events()
    assert event.category == "otp"
    assert event.event_number == 1
    assert event.metadata == {"attempts": 2, "otp_code": "[REDACTED]"}


def test_event_logger_disabled_returns_skipped_without_creating_database(tmp_path):
    db_path = tmp_path / "safedesk.sqlite3"
    logger = EventLogger(_config_for(db_path, enabled=False))

    result = logger.log_event("app", "manual_test", "info")

    assert result.success is False
    assert result.status == "skipped"
    assert db_path.exists() is False


def test_event_logger_write_failure_returns_safe_error(tmp_path):
    class FailingStore(SQLiteLogStore):
        def add_event(self, event):
            raise RuntimeError("database exploded with private details")

    logger = EventLogger(_config_for(tmp_path / "safedesk.sqlite3"), store=FailingStore(tmp_path / "safedesk.sqlite3"))

    result = logger.log_event("app", "manual_test", "info")

    assert result.success is False
    assert result.status == "storage_error"
    assert "private details" not in result.message

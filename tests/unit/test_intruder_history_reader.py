from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.intruder_history import IntruderHistoryReader


def _config_for_tmp(root: Path):
    return deep_merge(
        DEFAULT_CONFIG,
        {
            "intruder_detection": {
                "manifest_path": "data/config/intruder_capture_manifest.json",
                "intruder_images_dir": "data/intruders",
            }
        },
    )


def _write_manifest(root: Path, payload) -> None:
    path = root / "data" / "config" / "intruder_capture_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_missing_intruder_manifest_returns_empty_summary(tmp_path):
    reader = IntruderHistoryReader(_config_for_tmp(tmp_path), tmp_path)

    summary = reader.build_summary()

    assert summary.total_count == 0
    assert summary.items == ()
    assert summary.message == "No intruder evidence captured yet."


def test_valid_manifest_returns_sanitized_entries_without_display_paths(tmp_path):
    images_dir = tmp_path / "data" / "intruders"
    images_dir.mkdir(parents=True)
    image = images_dir / "intruder_2026-07-01-12-00-00_abcd1234.jpg"
    image.write_bytes(b"not a real image but present")
    _write_manifest(
        tmp_path,
        {
            "captures": [
                {
                    "capture_id": "abcd1234",
                    "created_at": "2026-07-01T12:00:00+00:00",
                    "relative_image_path": image.name,
                    "status": "unknown_detected",
                    "message": "Unknown/unverified local evidence.",
                    "event_number": 7,
                }
            ]
        },
    )

    summary = IntruderHistoryReader(_config_for_tmp(tmp_path), tmp_path).build_summary()
    item = summary.items[0]
    display_values = (item.capture_id, item.captured_at, item.status, item.safe_message, item.event_reference)

    assert summary.total_count == 1
    assert summary.image_available_count == 1
    assert item.image_available is True
    assert item.preview_allowed is True
    assert item.preview_path == image
    assert all(str(tmp_path) not in value for value in display_values)


def test_manifest_display_fields_hide_local_paths_but_keep_safe_fields(tmp_path):
    images_dir = tmp_path / "data" / "intruders"
    images_dir.mkdir(parents=True)
    image = images_dir / "intruder_safe.jpg"
    image.write_bytes(b"local test image")
    _write_manifest(
        tmp_path,
        {
            "captures": [
                {
                    "capture_id": "safe-capture-1",
                    "created_at": "2026-07-01T12:00:00+00:00",
                    "relative_image_path": image.name,
                    "status": "unknown_detected",
                    "reason": r"Stored beside C:\Users\owner\SafeDesk\data\intruders\intruder_safe.jpg",
                }
            ]
        },
    )

    item = IntruderHistoryReader(_config_for_tmp(tmp_path), tmp_path).build_summary().items[0]

    assert item.capture_id == "safe-capture-1"
    assert item.captured_at == "2026-07-01T12:00:00+00:00"
    assert item.status == "unknown_detected"
    assert item.preview_path == image
    assert "[local path hidden]" in item.safe_message
    assert "C:" not in item.safe_message
    assert "Users" not in item.safe_message
    assert "intruder_safe.jpg" not in item.safe_message


def test_manifest_display_fields_hide_project_data_paths(tmp_path):
    _write_manifest(
        tmp_path,
        {
            "captures": [
                {
                    "capture_id": "safe-capture-2",
                    "created_at": "2026-07-01T12:30:00+00:00",
                    "status": "captured",
                    "message": "Evidence available at data/intruders/intruder_hidden.jpg",
                }
            ]
        },
    )

    item = IntruderHistoryReader(_config_for_tmp(tmp_path), tmp_path).build_summary().items[0]

    assert item.capture_id == "safe-capture-2"
    assert item.status == "captured"
    assert "[local path hidden]" in item.safe_message
    assert "data/intruders" not in item.safe_message
    assert "intruder_hidden.jpg" not in item.safe_message


def test_missing_image_is_reported_without_preview(tmp_path):
    _write_manifest(
        tmp_path,
        {
            "captures": [
                {
                    "capture_id": "missing",
                    "created_at": "2026-07-01T12:00:00+00:00",
                    "relative_image_path": "intruder_missing.jpg",
                }
            ]
        },
    )

    item = IntruderHistoryReader(_config_for_tmp(tmp_path), tmp_path).build_summary().items[0]

    assert item.image_available is False
    assert item.preview_allowed is False
    assert item.preview_path is None


def test_outside_directory_image_path_is_rejected_for_preview(tmp_path):
    outside = tmp_path / "outside.jpg"
    outside.write_bytes(b"local test image")
    _write_manifest(
        tmp_path,
        {
            "captures": [
                {
                    "capture_id": "outside",
                    "created_at": "2026-07-01T12:00:00+00:00",
                    "relative_image_path": "../outside.jpg",
                }
            ]
        },
    )

    item = IntruderHistoryReader(_config_for_tmp(tmp_path), tmp_path).build_summary().items[0]

    assert item.image_available is False
    assert item.preview_allowed is False
    assert item.preview_path is None


def test_reader_handles_list_manifest_and_malformed_records_safely(tmp_path):
    _write_manifest(
        tmp_path,
        [
            "bad-record",
            {"capture_id": "ok", "captured_at": "2026-07-01T13:00:00+00:00", "image_filename": "missing.png"},
        ],
    )

    summary = IntruderHistoryReader(_config_for_tmp(tmp_path), tmp_path).build_summary()

    assert summary.total_count == 1
    assert summary.items[0].capture_id == "ok"

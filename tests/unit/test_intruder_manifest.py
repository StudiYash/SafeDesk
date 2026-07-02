from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.intruders.intruder_manifest import (
    build_intruder_capture_status,
    load_intruder_manifest,
    save_intruder_manifest,
)
from safedesk.intruders.intruder_models import IntruderEvidenceRecord


def test_missing_intruder_manifest_returns_empty_records(tmp_path):
    assert load_intruder_manifest(tmp_path / "manifest.json") == []


def test_save_intruder_manifest_uses_relative_paths_only(tmp_path):
    manifest_path = tmp_path / "config" / "intruder_capture_manifest.json"
    record = IntruderEvidenceRecord(
        capture_id="abcd1234",
        created_at="2026-07-01T10:00:00+00:00",
        image_filename="intruder_2026-07-01-10-00-00_abcd1234.jpg",
        relative_image_path="intruder_2026-07-01-10-00-00_abcd1234.jpg",
        image_format="jpg",
        image_index=1,
    )

    save_intruder_manifest(manifest_path, [record])
    raw = manifest_path.read_text(encoding="utf-8")
    payload = json.loads(raw)
    loaded = load_intruder_manifest(manifest_path)

    assert str(tmp_path) not in raw
    assert payload["captures"][0]["relative_image_path"] == record.relative_image_path
    assert loaded[0].capture_id == "abcd1234"


def test_build_intruder_capture_status_counts_valid_files(tmp_path):
    images_dir = tmp_path / "intruders"
    images_dir.mkdir()
    (images_dir / "intruder_2026-07-01-10-00-00_abcd1234.jpg").write_bytes(b"fake")
    (images_dir / "note.txt").write_text("ignore", encoding="utf-8")

    status = build_intruder_capture_status(images_dir, tmp_path / "manifest.json", enabled=True, demo_only=True)

    assert status.enabled is True
    assert status.demo_only is True
    assert status.image_count == 1
    assert status.images_dir_exists is True
    assert status.manifest_exists is False

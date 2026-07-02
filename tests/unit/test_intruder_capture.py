from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from PIL import Image

from safedesk.intruders.intruder_capture import save_intruder_evidence_frame


def test_intruder_capture_saves_synthetic_image_to_temp_folder(tmp_path):
    image = Image.new("RGB", (16, 16), color="red")
    images_dir = tmp_path / "intruders"
    manifest_path = tmp_path / "config" / "intruder_capture_manifest.json"

    result = save_intruder_evidence_frame(image, images_dir, manifest_path)

    assert result.success is True
    assert result.status == "captured"
    assert result.capture_id
    assert result.image_saved is True
    assert result.image_count == 1
    assert len(list(images_dir.glob("intruder_*.jpg"))) == 1


def test_intruder_capture_manifest_does_not_store_absolute_paths(tmp_path):
    image = Image.new("RGB", (16, 16), color="blue")
    manifest_path = tmp_path / "config" / "intruder_capture_manifest.json"

    result = save_intruder_evidence_frame(image, tmp_path / "intruders", manifest_path)
    raw = manifest_path.read_text(encoding="utf-8")
    payload = json.loads(raw)

    assert result.success is True
    assert str(tmp_path) not in raw
    assert payload["captures"][0]["capture_id"] == result.capture_id
    assert payload["captures"][0]["relative_image_path"].startswith("intruder_")


def test_intruder_capture_invalid_frame_returns_safe_failure(tmp_path):
    result = save_intruder_evidence_frame(None, tmp_path / "intruders", tmp_path / "manifest.json")

    assert result.success is False
    assert result.status == "invalid_frame"
    assert result.image_saved is False


def test_intruder_capture_rejects_invalid_quality(tmp_path):
    image = Image.new("RGB", (16, 16), color="green")

    result = save_intruder_evidence_frame(image, tmp_path / "intruders", tmp_path / "manifest.json", image_quality=True)

    assert result.success is False
    assert result.status == "blocked"

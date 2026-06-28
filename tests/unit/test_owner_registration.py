from pathlib import Path
import sys
import json

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.vision.owner_registration import save_owner_sample


def test_saving_synthetic_owner_sample_updates_manifest(tmp_path):
    Image = pytest.importorskip("PIL.Image")
    samples_dir = tmp_path / "samples"
    manifest_path = tmp_path / "owner_registration_manifest.json"
    image = Image.new("RGB", (32, 32), color=(40, 80, 120))

    first = save_owner_sample(image, samples_dir, manifest_path, required_samples=2)
    second = save_owner_sample(image, samples_dir, manifest_path, required_samples=2)

    assert first.success is True
    assert first.saved_path is not None
    assert first.saved_path.exists()
    assert second.success is True
    assert second.sample_count == 2
    assert second.registration_complete is True

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["sample_count"] == 2
    assert manifest["registration_complete"] is True
    assert len(manifest["sample_files"]) == 2


def test_owner_sample_save_rejects_invalid_format(tmp_path):
    result = save_owner_sample(object(), tmp_path / "samples", tmp_path / "manifest.json", required_samples=1, image_format="gif")

    assert result.success is False
    assert "Unsupported" in result.message


@pytest.mark.parametrize("quality", [0, 101, True])
def test_owner_sample_save_rejects_invalid_image_quality(tmp_path, quality):
    result = save_owner_sample(
        object(),
        tmp_path / "samples",
        tmp_path / "manifest.json",
        required_samples=1,
        image_quality=quality,
    )

    assert result.success is False
    assert "Image quality" in result.message

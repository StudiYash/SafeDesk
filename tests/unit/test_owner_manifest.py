from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.vision.owner_manifest import (
    OwnerRegistrationManifest,
    build_registration_status,
    load_owner_manifest,
    save_owner_manifest,
)


def test_missing_manifest_returns_incomplete_status(tmp_path):
    status = build_registration_status(tmp_path / "samples", tmp_path / "manifest.json", required_samples=5)

    assert status.registration_complete is False
    assert status.sample_count == 0
    assert status.required_sample_count == 5
    assert status.manifest_exists is False


def test_manifest_saves_safe_metadata_only(tmp_path):
    path = tmp_path / "manifest.json"
    manifest = OwnerRegistrationManifest(
        required_sample_count=2,
        sample_count=1,
        sample_files=("owner_sample_test.jpg",),
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
        registration_complete=False,
    )

    save_owner_manifest(path, manifest)
    loaded = load_owner_manifest(path)
    raw = json.loads(path.read_text(encoding="utf-8"))

    assert loaded.sample_count == 1
    assert loaded.sample_files == ("owner_sample_test.jpg",)
    forbidden = ("password", "otp", "panic", "secret", "encoding", "embedding", "threshold")
    assert not any(key in json.dumps(raw).lower() for key in forbidden)


def test_registration_status_counts_only_valid_owner_sample_images(tmp_path):
    samples_dir = tmp_path / "samples"
    samples_dir.mkdir()
    (samples_dir / "owner_sample_valid.jpg").write_bytes(b"sample")
    (samples_dir / "owner_sample_valid.jpeg").write_bytes(b"sample")
    (samples_dir / "owner_sample_valid.png").write_bytes(b"sample")
    (samples_dir / "owner_sample_invalid.gif").write_bytes(b"sample")
    (samples_dir / "random.jpg").write_bytes(b"sample")
    (samples_dir / "notes.txt").write_text("not a sample", encoding="utf-8")

    status = build_registration_status(samples_dir, tmp_path / "manifest.json", required_samples=3)

    assert status.sample_count == 3
    assert status.registration_complete is True

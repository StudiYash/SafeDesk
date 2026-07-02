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


def test_registration_status_ignores_stale_manifest_sample_count(tmp_path):
    samples_dir = tmp_path / "samples"
    samples_dir.mkdir()
    manifest_path = tmp_path / "manifest.json"
    sample_files = tuple(f"owner_sample_{index:02d}.jpg" for index in range(13))
    for sample_file in sample_files[:5]:
        (samples_dir / sample_file).write_bytes(b"sample")
    save_owner_manifest(
        manifest_path,
        OwnerRegistrationManifest(
            required_sample_count=5,
            sample_count=13,
            sample_files=sample_files,
            registration_complete=True,
        ),
    )

    status = build_registration_status(samples_dir, manifest_path, required_samples=5)

    assert status.sample_count == 5
    assert status.registration_complete is True


def test_registration_status_ignores_missing_manifest_entries(tmp_path):
    samples_dir = tmp_path / "samples"
    samples_dir.mkdir()
    manifest_path = tmp_path / "manifest.json"
    (samples_dir / "owner_sample_existing.jpg").write_bytes(b"sample")
    save_owner_manifest(
        manifest_path,
        OwnerRegistrationManifest(
            required_sample_count=2,
            sample_count=2,
            sample_files=("owner_sample_existing.jpg", "owner_sample_missing.jpg"),
            registration_complete=True,
        ),
    )

    status = build_registration_status(samples_dir, manifest_path, required_samples=2)

    assert status.sample_count == 1
    assert status.registration_complete is False


def test_registration_status_counts_actual_files_not_listed_in_manifest(tmp_path):
    samples_dir = tmp_path / "samples"
    samples_dir.mkdir()
    manifest_path = tmp_path / "manifest.json"
    (samples_dir / "owner_sample_manifest.jpg").write_bytes(b"sample")
    (samples_dir / "owner_sample_extra.png").write_bytes(b"sample")
    save_owner_manifest(
        manifest_path,
        OwnerRegistrationManifest(
            required_sample_count=2,
            sample_count=1,
            sample_files=("owner_sample_manifest.jpg",),
            registration_complete=False,
        ),
    )

    status = build_registration_status(samples_dir, manifest_path, required_samples=2)

    assert status.sample_count == 2
    assert status.registration_complete is True


def test_registration_status_does_not_double_count_duplicate_manifest_entries(tmp_path):
    samples_dir = tmp_path / "samples"
    samples_dir.mkdir()
    manifest_path = tmp_path / "manifest.json"
    (samples_dir / "owner_sample_duplicate.jpg").write_bytes(b"sample")
    save_owner_manifest(
        manifest_path,
        OwnerRegistrationManifest(
            required_sample_count=2,
            sample_count=3,
            sample_files=(
                "owner_sample_duplicate.jpg",
                "owner_sample_duplicate.jpg",
                str(samples_dir / "owner_sample_duplicate.jpg"),
            ),
            registration_complete=True,
        ),
    )

    status = build_registration_status(samples_dir, manifest_path, required_samples=2)

    assert status.sample_count == 1
    assert status.registration_complete is False


def test_registration_status_supported_extensions_include_jpg_jpeg_png(tmp_path):
    samples_dir = tmp_path / "samples"
    samples_dir.mkdir()
    (samples_dir / "owner_sample_one.jpg").write_bytes(b"sample")
    (samples_dir / "owner_sample_two.jpeg").write_bytes(b"sample")
    (samples_dir / "owner_sample_three.png").write_bytes(b"sample")

    status = build_registration_status(samples_dir, tmp_path / "manifest.json", required_samples=3)

    assert status.sample_count == 3
    assert status.registration_complete is True


def test_registration_status_does_not_include_full_local_paths(tmp_path):
    samples_dir = tmp_path / "samples"
    samples_dir.mkdir()
    (samples_dir / "owner_sample_safe.jpg").write_bytes(b"sample")

    status = build_registration_status(samples_dir, tmp_path / "manifest.json", required_samples=1)

    assert str(tmp_path) not in repr(status)

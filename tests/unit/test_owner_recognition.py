from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.vision.deepface_adapter import DeepFaceDependencyStatus, DeepFaceVerifyResult
from safedesk.vision.owner_recognition import (
    build_recognition_readiness,
    classify_recognition_distance,
    discover_owner_sample_paths,
    verify_owner_against_samples,
)


def _config(tmp_path, required=2):
    return deep_merge(
        DEFAULT_CONFIG,
        {
            "owner_face_registration": {
                "samples_dir": str(tmp_path / "samples"),
            },
            "owner_recognition": {
                "minimum_samples_required": required,
                "cache_dir": str(tmp_path / "cache"),
                "demo_threshold": 0.68,
                "uncertain_margin": 0.05,
            },
        },
    )


def _dependency_ready():
    return DeepFaceDependencyStatus(True, "ready")


def test_missing_owner_samples_returns_not_ready(tmp_path):
    readiness = build_recognition_readiness(_config(tmp_path), dependency_checker=_dependency_ready, root=tmp_path)

    assert readiness.ready is False
    assert readiness.sample_count == 0


def test_insufficient_owner_samples_returns_not_ready(tmp_path):
    samples = tmp_path / "samples"
    samples.mkdir()
    (samples / "owner_sample_one.jpg").write_bytes(b"fake")

    readiness = build_recognition_readiness(_config(tmp_path, required=2), dependency_checker=_dependency_ready, root=tmp_path)

    assert readiness.ready is False
    assert readiness.sample_count == 1


def test_valid_owner_sample_paths_discovered(tmp_path):
    samples = tmp_path / "samples"
    samples.mkdir()
    (samples / "owner_sample_one.jpg").write_bytes(b"fake")
    (samples / "owner_sample_two.png").write_bytes(b"fake")
    (samples / "random.jpg").write_bytes(b"fake")

    paths = discover_owner_sample_paths(samples)

    assert [path.name for path in paths] == ["owner_sample_one.jpg", "owner_sample_two.png"]


def test_distance_classification():
    assert classify_recognition_distance(0.40, 0.68, 0.05) == (True, False, "Owner appears recognized")
    assert classify_recognition_distance(0.67, 0.68, 0.05) == (False, True, "Recognition uncertain")
    assert classify_recognition_distance(0.90, 0.68, 0.05) == (False, False, "Owner not recognized")


def test_verify_owner_against_samples_uses_injected_verifier(tmp_path):
    samples = tmp_path / "samples"
    samples.mkdir()
    (samples / "owner_sample_one.jpg").write_bytes(b"fake")
    (samples / "owner_sample_two.jpg").write_bytes(b"fake")
    current = tmp_path / "current.jpg"
    current.write_bytes(b"fake")

    distances = {
        "owner_sample_one.jpg": 0.8,
        "owner_sample_two.jpg": 0.4,
    }

    def fake_verifier(_current, sample, _config):
        return DeepFaceVerifyResult(True, "ok", distance=distances[sample.name])

    result = verify_owner_against_samples(
        current,
        _config(tmp_path, required=2),
        verifier=fake_verifier,
        dependency_checker=_dependency_ready,
        root=tmp_path,
    )

    assert result.success is True
    assert result.recognized is True
    assert result.matched_sample == "owner_sample_two.jpg"
    assert result.samples_checked == 2

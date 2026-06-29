"""Owner face recognition demo foundation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from safedesk.storage.paths import project_root
from safedesk.vision.deepface_adapter import DeepFaceDependencyStatus, DeepFaceVerifyResult, check_deepface_dependency, verify_faces
from safedesk.vision.owner_manifest import is_valid_owner_sample_file


@dataclass(frozen=True)
class OwnerRecognitionReadiness:
    ready: bool
    message: str
    sample_count: int
    required_sample_count: int
    dependency_available: bool


@dataclass(frozen=True)
class OwnerRecognitionResult:
    success: bool
    ready: bool
    recognized: bool
    uncertain: bool
    best_distance: float | None
    matched_sample: str
    samples_checked: int
    message: str


def _resolve_path(value: str, root: Path | None = None) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (root or project_root()) / path


def discover_owner_sample_paths(samples_dir: Path) -> list[Path]:
    if not samples_dir.exists():
        return []
    return sorted(path for path in samples_dir.iterdir() if is_valid_owner_sample_file(path))


def classify_recognition_distance(distance: float, threshold: float, uncertain_margin: float) -> tuple[bool, bool, str]:
    if abs(distance - threshold) <= uncertain_margin:
        return False, True, "Recognition uncertain"
    if distance < threshold:
        return True, False, "Owner appears recognized"
    return False, False, "Owner not recognized"


def build_recognition_readiness(
    config: dict[str, Any],
    dependency_checker: Callable[[], DeepFaceDependencyStatus] = check_deepface_dependency,
    root: Path | None = None,
) -> OwnerRecognitionReadiness:
    recognition_config = config.get("owner_recognition", {})
    registration_config = config.get("owner_face_registration", {})
    samples_dir = _resolve_path(registration_config.get("samples_dir", "data/owner/samples"), root)
    required_samples = int(recognition_config.get("minimum_samples_required", 5))
    sample_count = len(discover_owner_sample_paths(samples_dir))
    dependency = dependency_checker()

    if not dependency.available:
        return OwnerRecognitionReadiness(False, dependency.message, sample_count, required_samples, False)
    if sample_count < required_samples:
        return OwnerRecognitionReadiness(
            False,
            f"Not ready: {sample_count} owner samples available, {required_samples} required.",
            sample_count,
            required_samples,
            True,
        )
    return OwnerRecognitionReadiness(True, "Recognition demo is ready for local verification.", sample_count, required_samples, True)


def _save_temp_frame(image_data: Any, cache_dir: Path) -> Path:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is not installed.") from exc

    if isinstance(image_data, Path):
        return image_data

    if isinstance(image_data, Image.Image):
        image = image_data
    else:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("OpenCV is not installed.") from exc
        image = Image.fromarray(cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB))

    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"recognition_frame_{uuid4().hex[:8]}.jpg"
    image.convert("RGB").save(path, format="JPEG", quality=90)
    return path


def verify_owner_against_samples(
    image_data: Any,
    config: dict[str, Any],
    verifier: Callable[[Any, Any, dict[str, Any]], DeepFaceVerifyResult] = verify_faces,
    dependency_checker: Callable[[], DeepFaceDependencyStatus] = check_deepface_dependency,
    root: Path | None = None,
) -> OwnerRecognitionResult:
    readiness = build_recognition_readiness(config, dependency_checker=dependency_checker, root=root)
    if not readiness.ready:
        return OwnerRecognitionResult(False, False, False, False, None, "", 0, readiness.message)

    recognition_config = config.get("owner_recognition", {})
    registration_config = config.get("owner_face_registration", {})
    base_root = root or project_root()
    samples_dir = _resolve_path(registration_config.get("samples_dir", "data/owner/samples"), base_root)
    cache_dir = _resolve_path(recognition_config.get("cache_dir", "data/cache/recognition"), base_root)
    sample_paths = discover_owner_sample_paths(samples_dir)

    temp_path: Path | None = None
    should_delete_temp = not isinstance(image_data, Path)
    try:
        current_image = image_data if isinstance(image_data, Path) else _save_temp_frame(image_data, cache_dir)
        temp_path = current_image if isinstance(current_image, Path) else None
        best_distance: float | None = None
        matched_sample = ""
        samples_checked = 0

        for sample_path in sample_paths:
            result = verifier(current_image, sample_path, recognition_config)
            if not result.success or result.distance is None:
                continue
            samples_checked += 1
            if best_distance is None or result.distance < best_distance:
                best_distance = result.distance
                matched_sample = sample_path.name

        if best_distance is None:
            return OwnerRecognitionResult(False, False, False, False, None, "", samples_checked, "Not ready: recognition could not compare samples.")

        threshold = float(recognition_config.get("demo_threshold", 0.68))
        uncertain_margin = float(recognition_config.get("uncertain_margin", 0.05))
        recognized, uncertain, message = classify_recognition_distance(best_distance, threshold, uncertain_margin)
        return OwnerRecognitionResult(
            True,
            True,
            recognized,
            uncertain,
            best_distance,
            matched_sample,
            samples_checked,
            message,
        )
    except Exception as exc:
        return OwnerRecognitionResult(False, False, False, False, None, "", 0, f"Not ready: {exc}")
    finally:
        if should_delete_temp and temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass

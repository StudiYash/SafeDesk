"""Owner face sample saving foundation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from typing import Any

from safedesk.vision.owner_manifest import (
    build_registration_status,
    load_owner_manifest,
    save_owner_manifest,
    update_manifest_with_sample,
)


@dataclass(frozen=True)
class OwnerSampleSaveResult:
    success: bool
    message: str
    saved_path: Path | None = None
    sample_count: int = 0
    registration_complete: bool = False


def _safe_filename(image_format: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid4().hex[:8]
    extension = "jpg" if image_format.lower() == "jpeg" else image_format.lower()
    return f"owner_sample_{timestamp}_{short_uuid}.{extension}"


def _to_pil_image(image_data: Any):
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is not installed.") from exc

    if isinstance(image_data, Image.Image):
        return image_data

    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is not installed.") from exc

    rgb_frame = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb_frame)


def save_owner_sample(
    image_data: Any,
    samples_dir: Path,
    manifest_path: Path,
    required_samples: int,
    image_format: str = "jpg",
    image_quality: int = 90,
) -> OwnerSampleSaveResult:
    """Save one owner sample and update the local manifest.

    This function does not detect, recognize, or encode faces.
    """

    image_format = image_format.lower()
    if image_format not in {"jpg", "png"}:
        return OwnerSampleSaveResult(False, "Unsupported image format.")
    if isinstance(image_quality, bool) or not isinstance(image_quality, int) or not 1 <= image_quality <= 100:
        return OwnerSampleSaveResult(False, "Image quality must be between 1 and 100.")
    if required_samples <= 0:
        return OwnerSampleSaveResult(False, "Required sample count must be positive.")

    try:
        image = _to_pil_image(image_data)
        samples_dir.mkdir(parents=True, exist_ok=True)
        filename = _safe_filename(image_format)
        saved_path = samples_dir / filename

        save_kwargs = {}
        if image_format == "jpg":
            image = image.convert("RGB")
            save_kwargs["quality"] = image_quality
            pil_format = "JPEG"
        else:
            pil_format = "PNG"

        image.save(saved_path, format=pil_format, **save_kwargs)
        manifest = load_owner_manifest(manifest_path)
        updated = update_manifest_with_sample(manifest, filename, required_samples)
        save_owner_manifest(manifest_path, updated)
        status = build_registration_status(samples_dir, manifest_path, required_samples)
    except Exception as exc:
        return OwnerSampleSaveResult(False, f"Owner sample could not be saved: {exc}")

    return OwnerSampleSaveResult(
        True,
        "Owner sample saved locally.",
        saved_path=saved_path,
        sample_count=status.sample_count,
        registration_complete=status.registration_complete,
    )

"""Local-only intruder evidence image capture foundation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import secrets
from typing import Any

from safedesk.intruders.intruder_manifest import load_intruder_manifest, save_intruder_manifest
from safedesk.intruders.intruder_models import IntruderCaptureResult, IntruderEvidenceRecord


def save_intruder_evidence_frame(
    image_data: Any,
    images_dir: Path,
    manifest_path: Path,
    image_format: str = "jpg",
    image_quality: int = 90,
) -> IntruderCaptureResult:
    """Save one local evidence image and update the ignored local manifest."""

    image_format = str(image_format).lower()
    if image_format not in {"jpg", "png"}:
        return IntruderCaptureResult(False, "blocked", "Intruder evidence capture skipped because image format is unsupported.")
    if isinstance(image_quality, bool) or not isinstance(image_quality, int) or not 1 <= image_quality <= 100:
        return IntruderCaptureResult(False, "blocked", "Intruder evidence capture skipped because image quality is invalid.")
    if image_data is None:
        return IntruderCaptureResult(False, "invalid_frame", "Intruder evidence capture skipped because the frame was invalid.")

    capture_id = secrets.token_hex(4)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    filename_timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    extension = "jpg" if image_format == "jpg" else "png"
    image_filename = f"intruder_{filename_timestamp}_{capture_id}.{extension}"

    try:
        image = _to_pil_image(image_data)
        images_dir.mkdir(parents=True, exist_ok=True)
        image_path = images_dir / image_filename
        if image_format == "jpg":
            image = image.convert("RGB")
            image.save(image_path, format="JPEG", quality=image_quality)
        else:
            image.save(image_path, format="PNG")

        records = load_intruder_manifest(manifest_path)
        record = IntruderEvidenceRecord(
            capture_id=capture_id,
            created_at=created_at,
            image_filename=image_filename,
            relative_image_path=image_filename,
            image_format=image_format,
            image_index=len(records) + 1,
        )
        records.append(record)
        save_intruder_manifest(manifest_path, records)
    except ValueError:
        return IntruderCaptureResult(False, "invalid_frame", "Intruder evidence capture skipped because the frame was invalid.")
    except Exception:
        return IntruderCaptureResult(False, "storage_error", "Intruder evidence image could not be saved locally.")

    return IntruderCaptureResult(
        True,
        "captured",
        "Intruder evidence image captured locally.",
        capture_id=capture_id,
        image_saved=True,
        image_count=len(records),
        created_at=created_at,
    )


def _to_pil_image(image_data: Any):
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is not installed.") from exc

    if isinstance(image_data, Image.Image):
        return image_data

    shape = getattr(image_data, "shape", None)
    if shape is None:
        raise ValueError("Invalid frame.")

    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is not installed.") from exc

    return Image.fromarray(cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB))

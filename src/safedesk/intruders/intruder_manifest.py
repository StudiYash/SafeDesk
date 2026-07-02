"""Local-only manifest helpers for intruder evidence captures."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from safedesk.intruders.intruder_models import IntruderCaptureStatus, IntruderEvidenceRecord

MANIFEST_VERSION = 1


def load_intruder_manifest(path: Path) -> list[IntruderEvidenceRecord]:
    """Load local evidence manifest records, returning an empty list on missing/corrupt data."""

    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload.get("captures", [])
        if not isinstance(records, list):
            return []
        loaded: list[IntruderEvidenceRecord] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            loaded.append(
                IntruderEvidenceRecord(
                    capture_id=str(record.get("capture_id", "")),
                    created_at=str(record.get("created_at", "")),
                    image_filename=str(record.get("image_filename", "")),
                    relative_image_path=str(record.get("relative_image_path", "")),
                    image_format=str(record.get("image_format", "")),
                    image_index=int(record.get("image_index", 0) or 0),
                )
            )
        return [record for record in loaded if record.capture_id and record.image_filename]
    except Exception:
        return []


def save_intruder_manifest(path: Path, records: list[IntruderEvidenceRecord]) -> None:
    """Save local evidence metadata without absolute private paths or image bytes."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "version": MANIFEST_VERSION,
        "captures": [asdict(record) for record in records],
    }
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


def build_intruder_capture_status(
    images_dir: Path,
    manifest_path: Path,
    enabled: bool = True,
    demo_only: bool = True,
) -> IntruderCaptureStatus:
    """Build a safe status summary for local intruder evidence captures."""

    records = load_intruder_manifest(manifest_path)
    image_count = _count_local_evidence_images(images_dir)
    count = max(image_count, len(records))
    if count:
        message = f"{count} local evidence capture(s) saved."
    else:
        message = "No local evidence captures saved."
    return IntruderCaptureStatus(
        enabled=enabled,
        demo_only=demo_only,
        image_count=count,
        images_dir_exists=images_dir.exists(),
        manifest_exists=manifest_path.exists(),
        message=message,
    )


def _count_local_evidence_images(images_dir: Path) -> int:
    if not images_dir.exists():
        return 0
    valid_suffixes = {".jpg", ".jpeg", ".png"}
    return sum(
        1
        for path in images_dir.iterdir()
        if path.is_file() and path.name.startswith("intruder_") and path.suffix.lower() in valid_suffixes
    )

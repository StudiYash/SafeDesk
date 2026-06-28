"""Local owner face registration manifest helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

VALID_SAMPLE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def is_valid_owner_sample_file(path: Path) -> bool:
    return path.is_file() and path.name.startswith("owner_sample_") and path.suffix.lower() in VALID_SAMPLE_SUFFIXES


@dataclass(frozen=True)
class OwnerRegistrationManifest:
    registration_version: int = 1
    required_sample_count: int = 5
    sample_count: int = 0
    sample_files: tuple[str, ...] = field(default_factory=tuple)
    created_at: str = ""
    updated_at: str = ""
    registration_complete: bool = False


@dataclass(frozen=True)
class OwnerRegistrationStatus:
    registration_complete: bool
    sample_count: int
    required_sample_count: int
    manifest_exists: bool
    samples_dir_exists: bool


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def load_owner_manifest(path: Path) -> OwnerRegistrationManifest:
    if not path.exists():
        return OwnerRegistrationManifest()

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    sample_files = tuple(str(item) for item in data.get("sample_files", ()))
    return OwnerRegistrationManifest(
        registration_version=int(data.get("registration_version", 1)),
        required_sample_count=int(data.get("required_sample_count", 5)),
        sample_count=int(data.get("sample_count", len(sample_files))),
        sample_files=sample_files,
        created_at=str(data.get("created_at", "")),
        updated_at=str(data.get("updated_at", "")),
        registration_complete=bool(data.get("registration_complete", False)),
    )


def save_owner_manifest(path: Path, manifest: OwnerRegistrationManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(manifest)
    data["sample_files"] = list(manifest.sample_files)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def update_manifest_with_sample(
    manifest: OwnerRegistrationManifest,
    sample_file: str,
    required_samples: int,
) -> OwnerRegistrationManifest:
    now = _now()
    created_at = manifest.created_at or now
    sample_files = tuple((*manifest.sample_files, sample_file))
    sample_count = len(sample_files)
    return OwnerRegistrationManifest(
        registration_version=manifest.registration_version,
        required_sample_count=required_samples,
        sample_count=sample_count,
        sample_files=sample_files,
        created_at=created_at,
        updated_at=now,
        registration_complete=sample_count >= required_samples,
    )


def build_registration_status(
    samples_dir: Path,
    manifest_path: Path,
    required_samples: int,
) -> OwnerRegistrationStatus:
    manifest_exists = manifest_path.exists()
    manifest = load_owner_manifest(manifest_path) if manifest_exists else OwnerRegistrationManifest(required_sample_count=required_samples)
    sample_count = manifest.sample_count
    if samples_dir.exists():
        sample_files_on_disk = [path for path in samples_dir.iterdir() if is_valid_owner_sample_file(path)]
        sample_count = max(sample_count, len(sample_files_on_disk))

    return OwnerRegistrationStatus(
        registration_complete=sample_count >= required_samples,
        sample_count=sample_count,
        required_sample_count=required_samples,
        manifest_exists=manifest_exists,
        samples_dir_exists=samples_dir.exists(),
    )

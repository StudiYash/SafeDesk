"""Models for local intruder evidence capture foundation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntruderEvidenceRecord:
    """Metadata for one local evidence capture.

    Paths are relative to the configured local evidence directory.
    """

    capture_id: str
    created_at: str
    image_filename: str
    relative_image_path: str
    image_format: str
    image_index: int


@dataclass(frozen=True)
class IntruderCaptureResult:
    """Result of trying to save one local evidence image."""

    success: bool
    status: str
    message: str
    capture_id: str = ""
    image_saved: bool = False
    image_count: int = 0
    created_at: str = ""


@dataclass(frozen=True)
class IntruderCaptureStatus:
    """Safe local evidence status for GUI summaries."""

    enabled: bool
    demo_only: bool
    image_count: int
    images_dir_exists: bool
    manifest_exists: bool
    message: str

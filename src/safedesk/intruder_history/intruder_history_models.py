"""Models for owner-only intruder evidence history review."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IntruderEvidenceItem:
    """Sanitized evidence item for Admin Console display."""

    capture_id: str
    captured_at: str
    status: str
    safe_message: str
    image_available: bool
    preview_allowed: bool
    event_reference: str = ""
    preview_path: Path | None = None


@dataclass(frozen=True)
class IntruderHistorySummary:
    """Safe evidence summary for owner/admin surfaces."""

    total_count: int
    image_available_count: int
    most_recent_capture: str
    items: tuple[IntruderEvidenceItem, ...]
    message: str

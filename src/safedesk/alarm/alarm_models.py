"""Safe models for the owner-controlled alarm preview foundation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AlarmPreviewStatus:
    """Owner-safe alarm preview status without local path details."""

    enabled: bool
    foundation_enabled: bool
    demo_only: bool
    manual_preview_enabled: bool
    automatic_trigger_enabled: bool
    allow_looping: bool
    preview_active: bool
    audio_configured: bool
    audio_available: bool
    beep_fallback_enabled: bool
    backend_available: bool
    max_preview_duration_seconds: int
    configured_volume: float
    message: str


@dataclass(frozen=True)
class AlarmPreviewOperationResult:
    """Safe result for one manual alarm preview operation."""

    success: bool
    status: str
    message: str
    preview_active: bool
    backend: str = "unavailable"
    used_fallback: bool = False
    duration_seconds: int = 0

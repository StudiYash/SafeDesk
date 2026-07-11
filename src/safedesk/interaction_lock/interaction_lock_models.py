"""Models for the SafeDesk safe interaction lock foundation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InteractionLockStatus:
    """Safe summary of interaction lock lifecycle state."""

    enabled: bool
    foundation_enabled: bool
    demo_only: bool
    active: bool
    focus_recovery_enabled: bool
    recovery_interval_seconds: float
    tick_count: int
    last_window_count: int
    message: str


@dataclass(frozen=True)
class InteractionLockOperationResult:
    """Safe result for interaction lock operations."""

    success: bool
    status: str
    message: str
    active: bool
    window_count: int = 0

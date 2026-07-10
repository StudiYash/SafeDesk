"""Models for fullscreen lockdown display presentation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DisplayBounds:
    """Safe display geometry without monitor names or hardware identifiers."""

    index: int
    x: int
    y: int
    width: int
    height: int
    primary: bool = False


@dataclass(frozen=True)
class LockdownDisplayStatus:
    """Safe public status for lockdown display presentation."""

    enabled: bool
    foundation_enabled: bool
    demo_only: bool
    fullscreen_enabled: bool
    multi_display_enabled: bool
    active: bool
    display_count: int
    window_count: int
    message: str


@dataclass(frozen=True)
class LockdownDisplayOperationResult:
    """Result for starting or stopping fullscreen lockdown windows."""

    success: bool
    status: str
    message: str
    display_count: int = 0
    window_count: int = 0
    fallback_used: bool = False

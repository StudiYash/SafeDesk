"""Models for the SafeDesk background-agent foundation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BackgroundAgentStatus:
    """Safe public status for background-agent/tray availability."""

    enabled: bool
    foundation_enabled: bool
    demo_only: bool
    system_tray_enabled: bool
    tray_available: bool
    tray_running: bool
    minimize_to_tray: bool
    close_to_tray: bool
    allow_exit_from_tray: bool
    message: str


@dataclass(frozen=True)
class TrayOperationResult:
    """Result for starting or stopping the optional tray controller."""

    success: bool
    status: str
    message: str
    tray_available: bool
    tray_running: bool

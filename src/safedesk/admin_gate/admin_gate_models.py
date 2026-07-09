"""Safe result models for the Owner/Admin Console gate."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdminGateStatus:
    """Safe status shown by the Owner/Admin Gate."""

    enabled: bool
    foundation_enabled: bool
    demo_only: bool
    password_configured: bool
    setup_required: bool
    locked_out: bool
    remaining_attempts: int
    lockout_remaining_seconds: int
    development_continue_allowed: bool
    message: str


@dataclass(frozen=True)
class AdminGateAttemptResult:
    """Safe result for an admin gate action."""

    success: bool
    status: str
    message: str
    remaining_attempts: int
    lockout_remaining_seconds: int

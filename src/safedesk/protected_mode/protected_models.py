"""Public-safe protected-mode foundation models."""

from __future__ import annotations

from dataclasses import dataclass

PROTECTED_MODE_STATES = (
    "inactive",
    "armed",
    "active_demo",
    "recovery_required",
    "recovery_successful",
    "reset",
)


@dataclass(frozen=True)
class ProtectedModeDefinition:
    """Safe wording for a protected-mode foundation state."""

    mode: str
    title: str
    description: str


PROTECTED_MODE_DEFINITIONS = (
    ProtectedModeDefinition("inactive", "Inactive", "No protected-mode foundation state is active."),
    ProtectedModeDefinition("armed", "Armed", "Protected-mode foundation is armed for manual demo testing only."),
    ProtectedModeDefinition("active_demo", "Active demo", "Protected-mode demo state is active. No enforcement is performed."),
    ProtectedModeDefinition("recovery_required", "Recovery required", "Recovery requirement is being simulated. No lock screen is active."),
    ProtectedModeDefinition("recovery_successful", "Recovery successful", "Recovery simulation completed successfully."),
    ProtectedModeDefinition("reset", "Reset to safe", "Protected-mode state was reset to inactive safe mode."),
)


@dataclass(frozen=True)
class ProtectedModeState:
    """Ignored local protected-mode state safe for JSON storage."""

    mode: str = "inactive"
    armed: bool = False
    active_demo: bool = False
    recovery_required: bool = False
    last_action: str = "initial"
    last_reason: str = "Protected mode foundation is inactive."
    updated_at: str = ""
    demo_only: bool = True
    threat_level_at_last_update: int = 0
    shutdown_candidate: bool = False
    lockdown_performed: bool = False
    shutdown_performed: bool = False


@dataclass(frozen=True)
class ProtectedModeActionResult:
    """Result of a manual protected-mode foundation action."""

    success: bool
    status: str
    previous_mode: str
    new_mode: str
    message: str
    state: ProtectedModeState


@dataclass(frozen=True)
class ProtectedModeStatus:
    """Safe status summary for GUI/dashboard display."""

    state: ProtectedModeState
    threat_level: int
    threat_recommendation: str
    activation_recommended: bool
    shutdown_candidate_recommended: bool
    foundation_enabled: bool
    demo_only: bool

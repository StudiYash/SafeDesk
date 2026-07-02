"""Public-safe threat foundation models."""

from __future__ import annotations

from dataclasses import dataclass

THREAT_EVENT_TYPES = (
    "unknown_unverified_face",
    "repeated_unknown_unverified_face",
    "failed_password_attempt",
    "failed_otp_attempt",
    "failed_panic_attempt",
    "forced_exit_attempt",
    "serious_follow_up_event",
    "manual_reset",
    "manual_test_event",
)


@dataclass(frozen=True)
class ThreatLevelDefinition:
    """Safe wording for a threat level in foundation mode."""

    level: int
    title: str
    description: str


THREAT_LEVEL_DEFINITIONS = (
    ThreatLevelDefinition(0, "Safe / idle", "No simulated elevated activity is currently recorded."),
    ThreatLevelDefinition(1, "Unknown or unverified activity observed", "A manual foundation event has been observed."),
    ThreatLevelDefinition(2, "Repeated unknown or unverified activity", "Repeated manual unknown/unverified activity has been simulated."),
    ThreatLevelDefinition(3, "Repeated failed authentication attempts", "Manual failed authentication attempt thresholds have been reached."),
    ThreatLevelDefinition(4, "Forceful access pattern candidate", "Manual forceful-access style activity has been simulated."),
    ThreatLevelDefinition(5, "Shutdown escalation candidate", "Demo-only shutdown escalation candidate reached. No shutdown is performed."),
)


@dataclass(frozen=True)
class ThreatEvent:
    """A manual threat-foundation simulation event."""

    event_type: str
    source: str = "gui"
    demo_only: bool = True


@dataclass(frozen=True)
class ThreatState:
    """Local demo-only threat state safe for ignored JSON storage."""

    current_level: int = 0
    highest_level: int = 0
    unknown_unverified_count: int = 0
    failed_password_count: int = 0
    failed_otp_count: int = 0
    failed_panic_count: int = 0
    forced_exit_count: int = 0
    last_reason: str = "Safe idle."
    updated_at: str = ""
    demo_only: bool = True


@dataclass(frozen=True)
class ThreatAssessmentResult:
    """Result of a local threat-foundation state update."""

    success: bool
    status: str
    previous_level: int
    new_level: int
    highest_level: int
    reason: str
    message: str
    state: ThreatState

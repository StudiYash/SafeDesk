"""Public-safe shutdown escalation dry-run models."""

from __future__ import annotations

from dataclasses import dataclass

SHUTDOWN_ESCALATION_STATES = (
    "idle",
    "candidate",
    "countdown_ready",
    "countdown_running",
    "cancelled",
    "recovery_cancelled",
    "blocked_by_config",
    "simulated_shutdown_completed",
    "reset",
)

SHUTDOWN_ACTIONS = (
    "mark_shutdown_candidate",
    "apply_protected_mode_candidate",
    "apply_threat_level_candidate",
    "prepare_demo_countdown",
    "start_demo_countdown",
    "tick_demo_countdown",
    "complete_demo_countdown_now",
    "cancel_countdown",
    "mark_recovery_successful",
    "reset",
    "refresh_status",
)


@dataclass(frozen=True)
class ShutdownEscalationDefinition:
    """Safe wording for a shutdown escalation foundation state."""

    mode: str
    title: str
    description: str


SHUTDOWN_ESCALATION_DEFINITIONS = (
    ShutdownEscalationDefinition("idle", "Idle", "No shutdown escalation dry-run state is active."),
    ShutdownEscalationDefinition("candidate", "Candidate", "A shutdown escalation candidate is marked for demo review only."),
    ShutdownEscalationDefinition("countdown_ready", "Countdown ready", "A demo countdown is prepared. No shutdown command is connected."),
    ShutdownEscalationDefinition("countdown_running", "Countdown running", "A dry-run countdown is running. No shutdown will be performed."),
    ShutdownEscalationDefinition("cancelled", "Cancelled", "The dry-run countdown or candidate state was cancelled."),
    ShutdownEscalationDefinition("recovery_cancelled", "Recovery cancelled", "A recovery simulation cancelled the dry-run shutdown path."),
    ShutdownEscalationDefinition("blocked_by_config", "Blocked by config", "Shutdown escalation dry-run was blocked by safe configuration."),
    ShutdownEscalationDefinition(
        "simulated_shutdown_completed",
        "Simulated completion",
        "The demo countdown completed. No shutdown was performed.",
    ),
    ShutdownEscalationDefinition("reset", "Reset", "Shutdown escalation state was reset to idle."),
)


@dataclass(frozen=True)
class ShutdownEscalationState:
    """Ignored local shutdown escalation state safe for JSON storage."""

    mode: str = "idle"
    shutdown_candidate: bool = False
    countdown_running: bool = False
    countdown_remaining_seconds: int = 0
    countdown_total_seconds: int = 0
    last_action: str = "initial"
    last_reason: str = "Shutdown escalation dry-run is idle."
    updated_at: str = ""
    demo_only: bool = True
    threat_level_at_last_update: int = 0
    protected_mode_at_last_update: str = "inactive"
    protected_shutdown_candidate: bool = False
    manual_confirmation_required: bool = True
    real_shutdown_enabled: bool = False
    real_shutdown_command_enabled: bool = False
    guarded_real_shutdown_ready: bool = False
    real_shutdown_confirmation_matched: bool = False
    real_shutdown_requested: bool = False
    real_shutdown_scheduled: bool = False
    real_shutdown_abort_requested: bool = False
    real_shutdown_aborted: bool = False
    real_shutdown_countdown_seconds: int = 0
    real_shutdown_platform: str = ""
    real_shutdown_result_status: str = "not_requested"
    real_shutdown_result_message: str = "Guarded real shutdown has not been requested."
    shutdown_performed: bool = False
    restart_performed: bool = False
    logoff_performed: bool = False
    lockdown_performed: bool = False
    alarm_performed: bool = False
    email_sent: bool = False


@dataclass(frozen=True)
class ShutdownEscalationActionResult:
    """Result of one manual shutdown escalation dry-run action."""

    success: bool
    status: str
    previous_mode: str
    new_mode: str
    message: str
    state: ShutdownEscalationState


@dataclass(frozen=True)
class ShutdownEscalationStatus:
    """Safe status summary for GUI/dashboard display."""

    state: ShutdownEscalationState
    threat_level: int
    protected_mode: str
    protected_shutdown_candidate: bool
    shutdown_recommended: bool
    foundation_enabled: bool
    demo_only: bool
    real_shutdown_enabled: bool
    real_shutdown_command_enabled: bool
    guarded_real_shutdown_ready: bool
    platform_supported: bool
    recommendation: str

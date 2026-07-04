"""Safe shutdown escalation dry-run foundation exports."""

from safedesk.shutdown_escalation.real_shutdown_executor import (
    RealShutdownExecutionResult,
    RealShutdownExecutor,
    abort_windows_shutdown,
    schedule_windows_shutdown,
)
from safedesk.shutdown_escalation.shutdown_guard import ShutdownGuardCheck, ShutdownGuardReport, evaluate_shutdown_guards
from safedesk.shutdown_escalation.shutdown_manager import (
    ShutdownEscalationManager,
    build_shutdown_escalation_manager_from_config,
)
from safedesk.shutdown_escalation.shutdown_models import (
    SHUTDOWN_ACTIONS,
    SHUTDOWN_ESCALATION_DEFINITIONS,
    SHUTDOWN_ESCALATION_STATES,
    ShutdownEscalationActionResult,
    ShutdownEscalationDefinition,
    ShutdownEscalationState,
    ShutdownEscalationStatus,
)
from safedesk.shutdown_escalation.shutdown_state import (
    default_shutdown_state,
    load_shutdown_state,
    resolve_shutdown_state_path,
    save_shutdown_state,
    shutdown_state_from_dict,
    shutdown_state_to_dict,
)

__all__ = [
    "SHUTDOWN_ACTIONS",
    "SHUTDOWN_ESCALATION_DEFINITIONS",
    "SHUTDOWN_ESCALATION_STATES",
    "RealShutdownExecutionResult",
    "RealShutdownExecutor",
    "ShutdownEscalationActionResult",
    "ShutdownEscalationDefinition",
    "ShutdownEscalationManager",
    "ShutdownEscalationState",
    "ShutdownEscalationStatus",
    "ShutdownGuardCheck",
    "ShutdownGuardReport",
    "abort_windows_shutdown",
    "build_shutdown_escalation_manager_from_config",
    "default_shutdown_state",
    "evaluate_shutdown_guards",
    "load_shutdown_state",
    "resolve_shutdown_state_path",
    "schedule_windows_shutdown",
    "save_shutdown_state",
    "shutdown_state_from_dict",
    "shutdown_state_to_dict",
]

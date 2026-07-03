"""Safe protected-mode foundation exports."""

from safedesk.protected_mode.protected_manager import ProtectedModeManager, build_protected_mode_manager_from_config
from safedesk.protected_mode.protected_models import (
    PROTECTED_MODE_DEFINITIONS,
    PROTECTED_MODE_STATES,
    ProtectedModeActionResult,
    ProtectedModeDefinition,
    ProtectedModeState,
    ProtectedModeStatus,
)
from safedesk.protected_mode.protected_state import (
    default_protected_mode_state,
    load_protected_mode_state,
    protected_mode_state_from_dict,
    protected_mode_state_to_dict,
    resolve_protected_mode_state_path,
    save_protected_mode_state,
)

__all__ = [
    "PROTECTED_MODE_DEFINITIONS",
    "PROTECTED_MODE_STATES",
    "ProtectedModeActionResult",
    "ProtectedModeDefinition",
    "ProtectedModeManager",
    "ProtectedModeState",
    "ProtectedModeStatus",
    "build_protected_mode_manager_from_config",
    "default_protected_mode_state",
    "load_protected_mode_state",
    "protected_mode_state_from_dict",
    "protected_mode_state_to_dict",
    "resolve_protected_mode_state_path",
    "save_protected_mode_state",
]

"""SafeDesk application mode foundation."""

from safedesk.app_modes.mode_manager import AppModeManager
from safedesk.app_modes.mode_models import (
    AppModeTransitionResult,
    SafeDeskMode,
    can_open_admin_console_from_launch,
    can_open_public_lock_placeholder,
    parse_app_mode,
)

__all__ = [
    "AppModeManager",
    "AppModeTransitionResult",
    "SafeDeskMode",
    "can_open_admin_console_from_launch",
    "can_open_public_lock_placeholder",
    "parse_app_mode",
]

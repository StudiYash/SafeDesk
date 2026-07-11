"""SafeDesk safe interaction-lock foundation."""

from safedesk.interaction_lock.interaction_lock_manager import SafeInteractionLockManager
from safedesk.interaction_lock.interaction_lock_models import (
    InteractionLockOperationResult,
    InteractionLockStatus,
)

__all__ = [
    "InteractionLockOperationResult",
    "InteractionLockStatus",
    "SafeInteractionLockManager",
]

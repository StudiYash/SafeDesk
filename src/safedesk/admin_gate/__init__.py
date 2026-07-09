"""Owner/Admin Console gate foundation."""

from safedesk.admin_gate.admin_gate_manager import AdminGateManager
from safedesk.admin_gate.admin_gate_models import AdminGateAttemptResult, AdminGateStatus

__all__ = [
    "AdminGateAttemptResult",
    "AdminGateManager",
    "AdminGateStatus",
]

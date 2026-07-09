"""SafeDesk background-agent and system-tray foundation."""

from safedesk.background_agent.background_agent_manager import BackgroundAgentManager
from safedesk.background_agent.background_agent_models import BackgroundAgentStatus, TrayOperationResult
from safedesk.background_agent.tray_controller import TrayController

__all__ = [
    "BackgroundAgentManager",
    "BackgroundAgentStatus",
    "TrayController",
    "TrayOperationResult",
]

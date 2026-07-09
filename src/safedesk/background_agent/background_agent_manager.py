"""Safe background-agent configuration manager."""

from __future__ import annotations

from safedesk.background_agent.background_agent_models import BackgroundAgentStatus


class BackgroundAgentManager:
    """Read Phase 19 background-agent config without starting persistence."""

    def __init__(self, config: dict):
        self.config = config
        raw_config = config.get("background_agent", {}) if isinstance(config, dict) else {}
        self.agent_config = raw_config if isinstance(raw_config, dict) else {}

    @property
    def enabled(self) -> bool:
        return self.agent_config.get("enabled", True) is True

    @property
    def foundation_enabled(self) -> bool:
        return self.agent_config.get("foundation_enabled", True) is True

    @property
    def demo_only(self) -> bool:
        return self.agent_config.get("demo_only", True) is True

    @property
    def system_tray_enabled(self) -> bool:
        return self.agent_config.get("system_tray_enabled", True) is True

    @property
    def minimize_to_tray(self) -> bool:
        return self.agent_config.get("minimize_to_tray", True) is True

    @property
    def close_to_tray(self) -> bool:
        return self.agent_config.get("close_to_tray", False) is True

    @property
    def allow_exit_from_tray(self) -> bool:
        return self.agent_config.get("allow_exit_from_tray", True) is True

    @property
    def show_tray_notifications(self) -> bool:
        return self.agent_config.get("show_tray_notifications", False) is True

    def should_attempt_tray(self) -> bool:
        """Return True only for owner-controlled Phase 19 tray startup."""

        return self.enabled and self.foundation_enabled and self.demo_only and self.system_tray_enabled

    def build_status(self, *, tray_available: bool = False, tray_running: bool = False) -> BackgroundAgentStatus:
        """Build a safe status object that does not expose local paths or errors."""

        if not self.enabled:
            message = "Background agent foundation is disabled."
        elif not self.foundation_enabled:
            message = "Background agent foundation is not available."
        elif not self.demo_only:
            message = "Background agent requires demo-only mode in this phase."
        elif not self.system_tray_enabled:
            message = "System tray support is disabled."
        elif tray_running:
            message = "System tray support is running."
        elif tray_available:
            message = "System tray support is available."
        else:
            message = "System tray support is unavailable."

        return BackgroundAgentStatus(
            enabled=self.enabled,
            foundation_enabled=self.foundation_enabled,
            demo_only=self.demo_only,
            system_tray_enabled=self.system_tray_enabled,
            tray_available=tray_available,
            tray_running=tray_running,
            minimize_to_tray=self.minimize_to_tray,
            close_to_tray=self.close_to_tray,
            allow_exit_from_tray=self.allow_exit_from_tray,
            message=message,
        )

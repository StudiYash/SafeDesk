"""Runtime policy for guarded SafeDesk Developer Tools."""

from __future__ import annotations

from safedesk.developer_tools.developer_tools_models import DeveloperToolsStatus


class DeveloperToolsPolicy:
    """Evaluate explicit development and demo-safe guards."""

    def __init__(self, config: dict, *, effective_environment: str | None = None):
        self.config = config if isinstance(config, dict) else {}
        self.effective_environment = effective_environment

    def build_status(self) -> DeveloperToolsStatus:
        app = self.config.get("app", {})
        security = self.config.get("security_mode", {})
        raw_tools = self.config.get("developer_tools", {})
        tools = raw_tools if isinstance(raw_tools, dict) else {}

        runtime_environment = (
            self.effective_environment
            if self.effective_environment is not None
            else app.get("environment")
        )
        environment_supported = runtime_environment == "development"
        demo_safe_mode = app.get("demo_safe_mode") is True
        security_mode_supported = security.get("default_mode") == "demo_safe"
        foundation_enabled = tools.get("enabled") is True
        demo_only = tools.get("demo_only") is True
        show_demo_screens = tools.get("show_demo_screens") is True
        show_runtime_diagnostics = tools.get("show_runtime_diagnostics") is True
        guards_pass = (
            environment_supported
            and demo_safe_mode
            and security_mode_supported
            and foundation_enabled
            and demo_only
        )
        landing_visible = guards_pass and (show_demo_screens or show_runtime_diagnostics)
        demo_routes_allowed = guards_pass and show_demo_screens
        diagnostics_visible = guards_pass and show_runtime_diagnostics

        if not guards_pass:
            message = "Developer Tools are unavailable under the current safe runtime policy."
        elif not landing_visible:
            message = "Developer Tools are hidden by local settings."
        else:
            message = "Developer Tools are available in guarded demo-safe development mode."

        return DeveloperToolsStatus(
            environment_supported=environment_supported,
            demo_safe_mode=demo_safe_mode,
            security_mode_supported=security_mode_supported,
            foundation_enabled=foundation_enabled,
            demo_only=demo_only,
            show_demo_screens=show_demo_screens,
            show_runtime_diagnostics=show_runtime_diagnostics,
            landing_visible=landing_visible,
            demo_routes_allowed=demo_routes_allowed,
            diagnostics_visible=diagnostics_visible,
            safe_message=message,
        )

    def landing_page_visible(self) -> bool:
        return self.build_status().landing_visible

    def demo_route_allowed(self) -> bool:
        return self.build_status().demo_routes_allowed

    def diagnostics_visible(self) -> bool:
        return self.build_status().diagnostics_visible

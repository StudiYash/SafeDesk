"""Guarded Developer Tools landing page for the Owner/Admin Console."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.developer_tools import DeveloperToolsDiagnostics, DeveloperToolsPolicy
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.gui.components.status_card import StatusCard
from safedesk.gui.navigation import DEVELOPER_ROUTE_NAMES, SCREEN_DEFINITION_BY_NAME
from safedesk.logging.event_logger import build_logger_from_config


class DeveloperToolsScreen(ctk.CTkFrame):
    def __init__(
        self,
        master,
        context: RuntimeContext,
        on_open_screen: Callable[[str], None],
    ):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.config = context.load_result.config
        self.on_open_screen = on_open_screen
        self.effective_environment = context.settings.environment
        self.policy = DeveloperToolsPolicy(
            self.config,
            effective_environment=self.effective_environment,
        )
        self.policy_status = self.policy.build_status()
        self.event_logger = build_logger_from_config(self.config)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        page = ScrollablePage(self, mousewheel_units=5)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)

        PageHeader(
            page,
            "Developer Tools",
            "Guarded demo and diagnostic tools for SafeDesk development mode.",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, ds.SPACE_MD))

        InfoBanner(
            page,
            "Demo-only. Owner/Admin Gate access remains required. These tools do not enable real shutdown, automatic alarm triggers, or protected enforcement.",
            kind="warning",
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, ds.SPACE_MD))

        if self.policy_status.diagnostics_visible:
            diagnostics = DeveloperToolsDiagnostics(
                self.config,
                effective_environment=self.effective_environment,
                configuration_valid=context.report.is_valid,
            ).build_summary()
            StatusCard(
                page,
                "Safe Runtime Diagnostics",
                [(item.label, item.value) for item in diagnostics.items],
                accent=ds.SAFEDESK_NEUTRAL,
            ).grid(row=2, column=0, sticky="ew", padx=4, pady=(0, ds.SPACE_MD))
        else:
            InfoBanner(page, "Runtime diagnostics are hidden by local settings.", kind="neutral").grid(
                row=2,
                column=0,
                sticky="ew",
                padx=4,
                pady=(0, ds.SPACE_MD),
            )

        demo_host = ctk.CTkFrame(page, **ds.card_kwargs())
        demo_host.grid(row=3, column=0, sticky="ew", padx=4, pady=(0, ds.SPACE_MD))
        demo_host.grid_columnconfigure((0, 1), weight=1, uniform="developer_routes")
        ctk.CTkLabel(
            demo_host,
            text="Demo Screens",
            text_color=ds.TEXT_PRIMARY,
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))

        if self.policy_status.demo_routes_allowed:
            for index, route in enumerate(sorted(DEVELOPER_ROUTE_NAMES, key=self._route_order)):
                definition = SCREEN_DEFINITION_BY_NAME[route]
                button = ctk.CTkButton(
                    demo_host,
                    text=definition.label,
                    command=lambda name=route: self._request_route(name),
                    **ds.secondary_button_kwargs(),
                )
                button.grid(
                    row=1 + index // 2,
                    column=index % 2,
                    sticky="ew",
                    padx=(ds.SPACE_LG if index % 2 == 0 else ds.SPACE_SM, ds.SPACE_SM if index % 2 == 0 else ds.SPACE_LG),
                    pady=ds.SPACE_SM,
                )
        else:
            ctk.CTkLabel(
                demo_host,
                text="Demo screens are hidden by local settings.",
                text_color=ds.TEXT_SECONDARY,
                anchor="w",
            ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))

        page.bind_descendants_for_scroll()
        self._log_event(
            "developer_tools_opened",
            "Developer Tools opened.",
            {
                "result_status": "opened",
                "diagnostics_visible": self.policy_status.diagnostics_visible,
                "demo_routes_allowed": self.policy_status.demo_routes_allowed,
            },
        )

    def _request_route(self, route: str) -> None:
        status = self.policy.build_status()
        if route not in DEVELOPER_ROUTE_NAMES or not status.demo_routes_allowed:
            self._log_event(
                "developer_tool_route_blocked",
                "A Developer Tools route was blocked by safe policy.",
                {"route": route, "result_status": "blocked", "demo_routes_allowed": False},
            )
            return
        self._log_event(
            "developer_tool_route_requested",
            "A guarded Developer Tools route was requested.",
            {"route": route, "result_status": "requested", "demo_routes_allowed": True},
        )
        self.on_open_screen(route)

    def _log_event(self, action: str, message: str, metadata: dict) -> None:
        try:
            self.event_logger.log_app_event(action=action, status="info", message=message, metadata=metadata)
        except Exception:
            pass

    @staticmethod
    def _route_order(route: str) -> int:
        order = tuple(
            name
            for name in SCREEN_DEFINITION_BY_NAME
            if name in DEVELOPER_ROUTE_NAMES
        )
        return order.index(route)

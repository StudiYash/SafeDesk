"""Owner/Admin Console dashboard screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.dashboard import DashboardService
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.gui.components.status_card import StatusCard
from safedesk.logging.event_logger import build_logger_from_config


class DashboardPlaceholderScreen(ctk.CTkFrame):
    """Owner-only SafeDesk readiness and recent activity dashboard."""

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.config = context.load_result.config
        self.summary = DashboardService(self.config).build_summary()
        self.event_logger = build_logger_from_config(self.config)
        self._log_dashboard_opened()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self, mousewheel_units=6)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)

        PageHeader(
            page,
            "Dashboard",
            "Owner-only overview of SafeDesk readiness and recent activity.",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 10))

        InfoBanner(
            page,
            "Read-only local summary. This screen does not start camera, recognition, alerts, lockdown, or shutdown actions.",
            kind="info",
            compact=True,
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 10))

        cards = ctk.CTkFrame(page, fg_color="transparent")
        cards.grid(row=2, column=0, sticky="ew")
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=1)

        for index, section in enumerate(self.summary.sections):
            rows = [(row.label, row.value) for row in section.rows]
            StatusCard(
                cards,
                section.title,
                rows,
                accent=section.accent or ds.SAFEDESK_NEUTRAL,
            ).grid(row=index // 2, column=index % 2, sticky="nsew", padx=4, pady=6)

        recent_panel = ctk.CTkFrame(page, **ds.card_kwargs())
        recent_panel.grid(row=3, column=0, sticky="ew", padx=4, pady=(12, 6))
        recent_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            recent_panel,
            text="Recent Events",
            text_color=ds.TEXT_PRIMARY,
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))

        if not self.summary.recent_events:
            ctk.CTkLabel(
                recent_panel,
                text="No recent local events available.",
                text_color=ds.TEXT_SECONDARY,
                anchor="w",
            ).grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))
        else:
            for index, event in enumerate(self.summary.recent_events, start=1):
                text = (
                    f"Event {event.event_number} | {event.timestamp} | {event.category} | "
                    f"{event.action} | {event.status} | {event.severity}\n{event.message}"
                )
                ctk.CTkLabel(
                    recent_panel,
                    text=text,
                    text_color=ds.TEXT_SECONDARY,
                    anchor="w",
                    justify="left",
                    wraplength=900,
                ).grid(row=index, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))

        page.bind_descendants_for_scroll()

    def _log_dashboard_opened(self) -> None:
        try:
            self.event_logger.log_app_event(
                action="dashboard_opened",
                status="info",
                message="Owner/Admin Dashboard opened.",
                metadata={
                    "recent_event_count": len(self.summary.recent_events),
                    "intruder_evidence_count": self.summary.intruder_history.total_count,
                },
            )
        except Exception:
            pass

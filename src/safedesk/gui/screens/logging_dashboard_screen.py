"""Manual local event logs dashboard."""

import json

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.gui.components.status_card import StatusCard
from safedesk.logging.dashboard_helpers import (
    ALL_FILTER,
    SORT_DIRECTIONS,
    SORT_FIELDS,
    build_filter_options,
    filter_search_sort_events,
    format_event_timestamp_for_display,
)
from safedesk.logging.event_logger import build_logger_from_config


class LoggingDashboardScreen(ctk.CTkFrame):
    """Read-only local SQLite event dashboard with search, filters, and stable numbering."""

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.config = context.load_result.config
        self.logging_config = self.config.get("logging", {})
        self.logger = build_logger_from_config(self.config)

        self.search_var = ctk.StringVar(value="")
        self.category_var = ctk.StringVar(value=ALL_FILTER)
        self.status_var = ctk.StringVar(value=ALL_FILTER)
        self.severity_var = ctk.StringVar(value=ALL_FILTER)
        self.action_var = ctk.StringVar(value=ALL_FILTER)
        self.source_var = ctk.StringVar(value=ALL_FILTER)
        self.sort_field_var = ctk.StringVar(value="Event Number")
        self.sort_direction_var = ctk.StringVar(value="Ascending")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.page = ScrollablePage(self, mousewheel_units=6)
        self.page.grid(row=0, column=0, sticky="nsew")
        self.page.grid_columnconfigure(0, weight=1)

        PageHeader(
            self.page,
            "Event Logs",
            "Review local SafeDesk foundation events stored in SQLite.",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 10))

        InfoBanner(
            self.page,
            "Local-only foundation logs. Sensitive metadata is redacted, and this screen does not start protected mode, "
            "intruder capture, alerts, lockdown, or shutdown.",
            kind="info",
            compact=True,
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 10))

        self.status_container = ctk.CTkFrame(self.page, fg_color="transparent")
        self.status_container.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self.status_container.grid_columnconfigure(0, weight=1)

        self._build_search_panel(row=3)

        actions = ctk.CTkFrame(self.page, **ds.card_kwargs())
        actions.grid(row=4, column=0, sticky="ew", padx=4, pady=6)
        for column in (0, 1):
            actions.grid_columnconfigure(column, weight=1, uniform="log_actions")
        ctk.CTkButton(
            actions,
            text="Refresh Logs",
            command=self.refresh_logs,
            **ds.secondary_button_kwargs(),
        ).grid(row=0, column=0, sticky="ew", padx=(ds.SPACE_LG, ds.SPACE_SM), pady=ds.SPACE_MD)
        ctk.CTkButton(
            actions,
            text="Create Test Log Event",
            command=self.create_test_log_event,
            **ds.primary_button_kwargs(),
        ).grid(row=0, column=1, sticky="ew", padx=(ds.SPACE_SM, ds.SPACE_LG), pady=ds.SPACE_MD)

        self.message_banner = InfoBanner(self.page, "Ready to review local foundation logs.", kind="neutral", compact=True)
        self.message_banner.grid(row=5, column=0, sticky="ew", padx=4, pady=(6, 10))

        self.summary_label = ctk.CTkLabel(
            self.page,
            text="Showing 0 of 0 events.",
            text_color=ds.TEXT_SECONDARY,
            anchor="w",
            font=ctk.CTkFont(size=ds.FONT_SMALL),
        )
        self.summary_label.grid(row=6, column=0, sticky="ew", padx=8, pady=(0, 6))

        self.events_frame = ctk.CTkFrame(self.page, fg_color="transparent")
        self.events_frame.grid(row=7, column=0, sticky="ew", padx=0, pady=0)
        self.events_frame.grid_columnconfigure(0, weight=1)

        self.refresh_logs()

    def _build_search_panel(self, row: int) -> None:
        panel = ctk.CTkFrame(self.page, **ds.card_kwargs())
        panel.grid(row=row, column=0, sticky="ew", padx=4, pady=6)
        for column in range(5):
            panel.grid_columnconfigure(column, weight=1)

        ctk.CTkLabel(
            panel,
            text="Search and Filter",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, columnspan=5, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_MD, ds.SPACE_XS))

        ctk.CTkLabel(
            panel,
            text="Search examples: otp, email, failed, password, manual_test_event, authentication, WARNING, success",
            text_color=ds.TEXT_MUTED,
            anchor="w",
            font=ctk.CTkFont(size=ds.FONT_SMALL),
        ).grid(row=1, column=0, columnspan=5, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))

        self.search_entry = ctk.CTkEntry(
            panel,
            textvariable=self.search_var,
            placeholder_text="Search event number, timestamp, category, action, status, message, source, or sanitized metadata",
            fg_color=ds.CARD_BG_ALT,
            text_color=ds.TEXT_PRIMARY,
            border_color=ds.BORDER_MUTED,
        )
        self.search_entry.grid(row=2, column=0, columnspan=3, sticky="ew", padx=(ds.SPACE_LG, ds.SPACE_SM), pady=(0, ds.SPACE_SM))
        self.search_entry.bind("<Return>", lambda _event: self.refresh_logs())

        ctk.CTkButton(
            panel,
            text="Search",
            command=self.refresh_logs,
            **ds.primary_button_kwargs(),
        ).grid(row=2, column=3, sticky="ew", padx=ds.SPACE_SM, pady=(0, ds.SPACE_SM))
        ctk.CTkButton(
            panel,
            text="Reset Filters",
            command=self.reset_filters,
            **ds.secondary_button_kwargs(),
        ).grid(row=2, column=4, sticky="ew", padx=(ds.SPACE_SM, ds.SPACE_LG), pady=(0, ds.SPACE_SM))

        self.category_menu = self._add_filter_menu(panel, "Category", self.category_var, row=3, column=0)
        self.status_menu = self._add_filter_menu(panel, "Status", self.status_var, row=3, column=1)
        self.severity_menu = self._add_filter_menu(panel, "Severity", self.severity_var, row=3, column=2)
        self.action_menu = self._add_filter_menu(panel, "Action", self.action_var, row=3, column=3)
        self.source_menu = self._add_filter_menu(panel, "Source", self.source_var, row=3, column=4)

        self.sort_field_menu = self._add_filter_menu(panel, "Sort By", self.sort_field_var, row=5, column=0, values=list(SORT_FIELDS))
        self.sort_direction_menu = self._add_filter_menu(
            panel,
            "Direction",
            self.sort_direction_var,
            row=5,
            column=1,
            values=list(SORT_DIRECTIONS),
        )

    def _add_filter_menu(self, master, label: str, variable: ctk.StringVar, row: int, column: int, values: list[str] | None = None):
        ctk.CTkLabel(
            master,
            text=label,
            text_color=ds.TEXT_MUTED,
            font=ctk.CTkFont(size=ds.FONT_SMALL),
            anchor="w",
        ).grid(row=row, column=column, sticky="ew", padx=ds.SPACE_SM if column else ds.SPACE_LG, pady=(0, 2))
        menu = ctk.CTkOptionMenu(
            master,
            variable=variable,
            values=values or [ALL_FILTER],
            command=lambda _choice: self.refresh_logs(),
            fg_color=ds.CARD_BG_ALT,
            button_color=ds.BORDER_MUTED,
            button_hover_color=ds.SAFEDESK_RED,
            text_color=ds.TEXT_PRIMARY,
            dropdown_fg_color=ds.CARD_BG,
            dropdown_hover_color=ds.CARD_BG_ALT,
            dropdown_text_color=ds.TEXT_PRIMARY,
        )
        right_pad = ds.SPACE_LG if column == 4 else ds.SPACE_SM
        menu.grid(row=row + 1, column=column, sticky="ew", padx=(ds.SPACE_SM if column else ds.SPACE_LG, right_pad), pady=(0, ds.SPACE_MD))
        return menu

    def reset_filters(self) -> None:
        self.search_var.set("")
        self.category_var.set(ALL_FILTER)
        self.status_var.set(ALL_FILTER)
        self.severity_var.set(ALL_FILTER)
        self.action_var.set(ALL_FILTER)
        self.source_var.set(ALL_FILTER)
        self.sort_field_var.set("Event Number")
        self.sort_direction_var.set("Ascending")
        self.refresh_logs()

    def refresh_logs(self) -> None:
        for child in self.status_container.winfo_children():
            child.destroy()
        for child in self.events_frame.winfo_children():
            child.destroy()

        status = self.logger.store.build_status(enabled=self.logging_config.get("enabled", True))
        StatusCard(
            self.status_container,
            "Logging Status",
            [
                ("Logging", "enabled" if status.enabled else "disabled"),
                ("Database", "ready" if status.database_ready else "missing / not initialized"),
                ("Stored events", str(status.event_count)),
                ("Mode", "demo / foundation only" if self.logging_config.get("demo_only", True) else "review required"),
            ],
            accent=ds.SAFEDESK_NEUTRAL,
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=6)

        events = self.logger.store.list_events()
        self._update_filter_options(events)
        filters = {
            "category": self.category_var.get(),
            "status": self.status_var.get(),
            "severity": self.severity_var.get(),
            "action": self.action_var.get(),
            "source": self.source_var.get(),
        }
        visible_events = filter_search_sort_events(
            events,
            filters,
            self.search_var.get(),
            self.sort_field_var.get(),
            self.sort_direction_var.get(),
        )

        if self.search_var.get().strip() or any(value != ALL_FILTER for value in filters.values()):
            self.summary_label.configure(text=f"Showing {len(visible_events)} of {len(events)} events after filters/search.")
        else:
            self.summary_label.configure(text=f"Showing {len(visible_events)} of {len(events)} events.")

        if not visible_events:
            InfoBanner(
                self.events_frame,
                "No local events match the current search and filters." if events else "No local events have been recorded yet.",
                kind="neutral",
                compact=True,
            ).grid(row=0, column=0, sticky="ew", padx=4, pady=6)
            self.page.bind_descendants_for_scroll()
            return

        for index, event in enumerate(visible_events):
            metadata_text = json.dumps(event.metadata, sort_keys=True)
            rows = [
                ("Timestamp", format_event_timestamp_for_display(event.timestamp)),
                ("Category", event.category),
                ("Action", event.action),
                ("Status", event.status),
                ("Severity", event.severity),
                ("Source", event.source),
                ("Message", event.message or "No message"),
            ]
            if metadata_text != "{}":
                rows.append(("Metadata", metadata_text))
            StatusCard(
                self.events_frame,
                f"Event {event.event_number}",
                rows,
                accent=ds.SAFEDESK_ALERT if event.severity in {"WARNING", "ERROR"} else ds.SAFEDESK_NEUTRAL,
            ).grid(row=index, column=0, sticky="ew", padx=4, pady=6)
        self.page.bind_descendants_for_scroll()

    def _update_filter_options(self, events) -> None:
        options = build_filter_options(events)
        self._configure_filter_menu(self.category_menu, self.category_var, options["category"])
        self._configure_filter_menu(self.status_menu, self.status_var, options["status"])
        self._configure_filter_menu(self.severity_menu, self.severity_var, options["severity"])
        self._configure_filter_menu(self.action_menu, self.action_var, options["action"])
        self._configure_filter_menu(self.source_menu, self.source_var, options["source"])

    @staticmethod
    def _configure_filter_menu(menu, variable: ctk.StringVar, values: list[str]) -> None:
        menu.configure(values=values)
        if variable.get() not in values:
            variable.set(ALL_FILTER)

    def create_test_log_event(self) -> None:
        result = self.logger.log_app_event(
            action="manual_test_event",
            status="info",
            message="Manual test event created from Event Logs dashboard.",
            metadata={"trigger": "event_logs_dashboard"},
        )
        self.message_banner.set_message(result.message)
        self.refresh_logs()

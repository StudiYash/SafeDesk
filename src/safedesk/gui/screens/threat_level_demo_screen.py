"""Manual threat level and forceful-access simulation foundation screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.threats import THREAT_LEVEL_DEFINITIONS, ThreatAssessmentResult, ThreatManager


class ThreatLevelDemoScreen(ctk.CTkFrame):
    """Manual threat foundation simulator with no enforcement behavior."""

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.config = context.load_result.config
        self.threat_config = self.config.get("threat_levels", {})
        self.threat_manager = ThreatManager(self.config)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=1)

        PageHeader(
            page,
            "Threat Level Demo",
            "Manually simulate threat-foundation events and review local demo-only escalation state.",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 10))

        InfoBanner(
            page,
            "Foundation demo only. This screen does not start protected mode, shutdown, lockdown, alarm, email, camera monitoring, or input blocking.",
            kind="warning",
            compact=True,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 12))

        left_panel = ctk.CTkFrame(page, **ds.card_kwargs())
        left_panel.grid(row=2, column=0, sticky="nsew", padx=(4, 8), pady=0)
        left_panel.grid_columnconfigure(0, weight=1)

        right_panel = ctk.CTkFrame(page, **ds.card_kwargs())
        right_panel.grid(row=2, column=1, sticky="nsew", padx=(8, 4), pady=0)
        right_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_panel,
            text="Current State",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))

        self.status_label = ctk.CTkLabel(
            left_panel,
            text="",
            justify="left",
            anchor="w",
            text_color=ds.TEXT_SECONDARY,
            wraplength=410,
            font=ctk.CTkFont(size=ds.FONT_SMALL),
        )
        self.status_label.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_MD))

        self.result_panel = ctk.CTkFrame(left_panel, **ds.panel_kwargs())
        self.result_panel.grid(row=2, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_MD))
        self.result_panel.grid_columnconfigure(0, weight=1)
        self.result_label = ctk.CTkLabel(
            self.result_panel,
            text="Last threat simulation: not run yet",
            justify="left",
            anchor="w",
            text_color=ds.TEXT_PRIMARY,
            wraplength=390,
            font=ctk.CTkFont(size=ds.FONT_SMALL),
        )
        self.result_label.grid(row=0, column=0, sticky="ew", padx=ds.SPACE_MD, pady=ds.SPACE_SM)

        self.message_banner = InfoBanner(
            left_panel,
            "Use manual simulation buttons to update local demo threat state. No enforcement action is connected.",
            kind="neutral",
            compact=True,
            wraplength=390,
        )
        self.message_banner.grid(row=3, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))

        ctk.CTkLabel(
            right_panel,
            text="Manual Simulations",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))

        button_grid = ctk.CTkFrame(right_panel, fg_color="transparent")
        button_grid.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_MD))
        for column in (0, 1):
            button_grid.grid_columnconfigure(column, weight=1)

        buttons = (
            ("Simulate Unknown/Unverified Face", "unknown_unverified_face", 0, 0),
            ("Simulate Failed Password Attempt", "failed_password_attempt", 0, 1),
            ("Simulate Failed OTP Attempt", "failed_otp_attempt", 1, 0),
            ("Simulate Failed Panic Attempt", "failed_panic_attempt", 1, 1),
            ("Simulate Forced Exit Attempt", "forced_exit_attempt", 2, 0),
            ("Simulate Serious Follow-up Event", "serious_follow_up_event", 2, 1),
        )
        for text, event_type, row, column in buttons:
            button = ctk.CTkButton(
                button_grid,
                text=text,
                command=lambda event_type=event_type: self.simulate_event(event_type),
                **ds.primary_button_kwargs(),
            )
            button.grid(row=row, column=column, sticky="ew", padx=(0 if column == 0 else 6, 6 if column == 0 else 0), pady=(0, 8))

        utility_row = ctk.CTkFrame(right_panel, fg_color="transparent")
        utility_row.grid(row=2, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))
        utility_row.grid_columnconfigure(0, weight=1)
        utility_row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(utility_row, text="Reset Threat State", command=self.reset_threat_state, **ds.secondary_button_kwargs()).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        ctk.CTkButton(utility_row, text="Refresh Status", command=self.refresh_status, **ds.secondary_button_kwargs()).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        self.refresh_status()

    def simulate_event(self, event_type: str) -> None:
        result = self.threat_manager.record_event(event_type)
        self._display_result(event_type, result)
        self.refresh_status()

    def reset_threat_state(self) -> None:
        result = self.threat_manager.reset_state()
        self._display_result("manual_reset", result)
        self.refresh_status()

    def refresh_status(self) -> None:
        state = self.threat_manager.load_state()
        level_title = self._level_title(state.current_level)
        shutdown_candidate = "yes" if state.current_level >= 5 else "no"
        self.status_label.configure(
            text=(
                f"Current level: {state.current_level} - {level_title}\n"
                f"Highest level: {state.highest_level}\n"
                f"Last reason: {state.last_reason}\n"
                f"Unknown/unverified count: {state.unknown_unverified_count}\n"
                f"Failed password count: {state.failed_password_count}\n"
                f"Failed OTP count: {state.failed_otp_count}\n"
                f"Failed panic count: {state.failed_panic_count}\n"
                f"Forced exit count: {state.forced_exit_count}\n"
                f"Threat foundation: {'available' if self.threat_config.get('foundation_enabled', True) else 'disabled'}\n"
                f"Final automatic threat system: not connected\n"
                f"Shutdown candidate: {shutdown_candidate}; shutdown performed: no"
            )
        )

    def _display_result(self, event_type: str, result: ThreatAssessmentResult) -> None:
        self.message_banner.set_message(result.message)
        self.result_label.configure(
            text=(
                f"Last threat simulation: {event_type}\n"
                f"Status: {result.status}\n"
                f"Previous level: {result.previous_level}\n"
                f"New level: {result.new_level}\n"
                f"Highest level: {result.highest_level}\n"
                f"Reason: {result.reason}\n"
                "Protected mode active: no\n"
                "Shutdown performed: no"
            )
        )

    @staticmethod
    def _level_title(level: int) -> str:
        for definition in THREAT_LEVEL_DEFINITIONS:
            if definition.level == level:
                return definition.title
        return "Unknown foundation level"

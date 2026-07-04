"""Shutdown escalation dry-run and guarded manual shutdown screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.shutdown_escalation import ShutdownEscalationActionResult, ShutdownEscalationManager


class ShutdownEscalationScreen(ctk.CTkFrame):
    """Manual shutdown escalation screen with dry-run controls and a guarded real shutdown test section."""

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.config = context.load_result.config
        self.manager = ShutdownEscalationManager(self.config)
        self.countdown_after_id: str | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=1)

        PageHeader(
            page,
            "Shutdown Escalation Demo",
            "Model dry-run shutdown escalation locally, with real Windows shutdown available only through the separate guarded manual test.",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 10))

        InfoBanner(
            page,
            "Dry-run controls never perform real shutdown. Manual guarded real shutdown is disabled by default and can run only from "
            "the separate test section after local opt-in, guard readiness, and the exact confirmation phrase. No automatic shutdown "
            "is connected to threat level, protected mode, intruder detection, recognition, liveness, dashboard, or app startup.",
            kind="danger",
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
            text="Shutdown Dry-Run State",
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
            text="Last shutdown dry-run action: not run yet",
            justify="left",
            anchor="w",
            text_color=ds.TEXT_PRIMARY,
            wraplength=390,
            font=ctk.CTkFont(size=ds.FONT_SMALL),
        )
        self.result_label.grid(row=0, column=0, sticky="ew", padx=ds.SPACE_MD, pady=ds.SPACE_SM)

        self.message_banner = InfoBanner(
            left_panel,
            "Dry-run controls never perform real shutdown. Manual guarded real shutdown is available only in the separate test section when all local guards pass.",
            kind="neutral",
            compact=True,
            wraplength=390,
        )
        self.message_banner.grid(row=3, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))

        ctk.CTkLabel(
            right_panel,
            text="Manual Dry-Run Actions",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))

        button_grid = ctk.CTkFrame(right_panel, fg_color="transparent")
        button_grid.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_MD))
        for column in (0, 1):
            button_grid.grid_columnconfigure(column, weight=1)

        buttons = (
            ("Mark Shutdown Candidate", "mark_shutdown_candidate", 0, 0),
            ("Apply Protected Mode Candidate", "apply_protected_mode_candidate", 0, 1),
            ("Apply Threat Level Candidate", "apply_threat_level_candidate", 1, 0),
            ("Prepare Demo Countdown", "prepare_demo_countdown", 1, 1),
            ("Start Demo Countdown", "start_demo_countdown", 2, 0),
            ("Complete Countdown Now", "complete_demo_countdown_now", 2, 1),
            ("Cancel Countdown", "cancel_countdown", 3, 0),
            ("Mark Recovery Successful", "mark_recovery_successful", 3, 1),
        )
        for text, action, row, column in buttons:
            button = ctk.CTkButton(
                button_grid,
                text=text,
                command=lambda action=action: self.perform_action(action),
                **ds.primary_button_kwargs(),
            )
            button.grid(row=row, column=column, sticky="ew", padx=(0 if column == 0 else 6, 6 if column == 0 else 0), pady=(0, 8))

        utility_row = ctk.CTkFrame(right_panel, fg_color="transparent")
        utility_row.grid(row=2, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))
        utility_row.grid_columnconfigure(0, weight=1)
        utility_row.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(utility_row, text="Reset Shutdown State", command=lambda: self.perform_action("reset"), **ds.secondary_button_kwargs()).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        ctk.CTkButton(utility_row, text="Refresh Status", command=self.refresh_status, **ds.secondary_button_kwargs()).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        real_panel = ctk.CTkFrame(right_panel, **ds.panel_kwargs())
        real_panel.grid(row=3, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))
        real_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            real_panel,
            text="Guarded Real Shutdown Test",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_MD, pady=(ds.SPACE_MD, ds.SPACE_XS))

        self.real_warning_banner = InfoBanner(
            real_panel,
            "This will schedule a real Windows shutdown if all local guards are enabled and the exact phrase is entered. Save your work first. "
            "No automatic shutdown is connected to threat/protected mode or other SafeDesk screens. Use Abort Pending Real Shutdown to cancel a scheduled Windows shutdown.",
            kind="warning",
            compact=True,
            wraplength=390,
        )
        self.real_warning_banner.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_MD, pady=(0, ds.SPACE_SM))

        self.guard_label = ctk.CTkLabel(
            real_panel,
            text="",
            justify="left",
            anchor="w",
            text_color=ds.TEXT_SECONDARY,
            wraplength=390,
            font=ctk.CTkFont(size=ds.FONT_SMALL),
        )
        self.guard_label.grid(row=2, column=0, sticky="ew", padx=ds.SPACE_MD, pady=(0, ds.SPACE_SM))

        self.confirmation_entry = ctk.CTkEntry(
            real_panel,
            placeholder_text="Type confirmation phrase",
            fg_color=ds.CARD_BG_ALT,
            border_color=ds.BORDER_MUTED,
            text_color=ds.TEXT_PRIMARY,
        )
        self.confirmation_entry.grid(row=3, column=0, sticky="ew", padx=ds.SPACE_MD, pady=(0, ds.SPACE_SM))

        real_button_grid = ctk.CTkFrame(real_panel, fg_color="transparent")
        real_button_grid.grid(row=4, column=0, sticky="ew", padx=ds.SPACE_MD, pady=(0, ds.SPACE_MD))
        for column in (0, 1):
            real_button_grid.grid_columnconfigure(column, weight=1)
        ctk.CTkButton(
            real_button_grid,
            text="Check Real Shutdown Guards",
            command=self.check_real_shutdown_guards,
            **ds.secondary_button_kwargs(),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 8))
        ctk.CTkButton(
            real_button_grid,
            text="Request Guarded Real Shutdown",
            command=self.request_guarded_real_shutdown,
            fg_color=ds.SAFEDESK_DEEP_RED,
            hover_color=ds.SAFEDESK_RED,
            text_color=ds.TEXT_PRIMARY,
            corner_radius=ds.RADIUS_SM,
            border_width=0,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=(0, 8))
        ctk.CTkButton(
            real_button_grid,
            text="Abort Pending Real Shutdown",
            command=self.abort_pending_real_shutdown,
            **ds.secondary_button_kwargs(),
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 0))

        self.refresh_status()

    def perform_action(self, action: str) -> None:
        if action in {"cancel_countdown", "complete_demo_countdown_now", "mark_recovery_successful", "reset"}:
            self._cancel_countdown_timer()
        result = self.manager.perform_action(action)
        self._display_result(action, result)
        self.refresh_status()
        if action == "start_demo_countdown" and result.success and result.state.countdown_running:
            self._schedule_countdown_tick()

    def refresh_status(self) -> None:
        status = self.manager.build_status()
        state = status.state
        guard_report = self.manager.evaluate_real_shutdown_guards()
        guard_lookup = {check.name: check.passed for check in guard_report.checks}
        self.status_label.configure(
            text=(
                f"Current mode: {state.mode}\n"
                f"Shutdown candidate: {'yes' if state.shutdown_candidate else 'no'}\n"
                f"Countdown running: {'yes' if state.countdown_running else 'no'}\n"
                f"Countdown remaining: {state.countdown_remaining_seconds}s / {state.countdown_total_seconds}s\n"
                f"Current threat level: {status.threat_level}\n"
                f"Protected mode: {status.protected_mode}\n"
                f"Protected shutdown candidate: {'yes' if status.protected_shutdown_candidate else 'no'}\n"
                f"Recommendation: {status.recommendation}\n"
                f"Real shutdown enabled: {'yes' if status.real_shutdown_enabled else 'no'}\n"
                f"Real command enabled: {'yes' if status.real_shutdown_command_enabled else 'no'}\n"
                f"Guarded real shutdown ready: {'yes' if status.guarded_real_shutdown_ready else 'no'}\n"
                f"Real shutdown scheduled: {'yes' if state.real_shutdown_scheduled else 'no'}\n"
                f"Abort requested: {'yes' if state.real_shutdown_abort_requested else 'no'}\n"
                "Shutdown performed: no\n"
                "Restart performed: no\n"
                "Logoff performed: no\n"
                "Lockdown performed: no\n"
                "Alarm performed: no\n"
                "Email sent: no\n"
                f"Demo-only mode: {'yes' if status.demo_only else 'review required'}\n"
                "Automatic real shutdown execution: not connected"
            )
        )
        self.guard_label.configure(
            text=(
                f"Final status: {'ready' if guard_report.ready else 'blocked'}\n"
                f"Platform supported: {'yes' if guard_report.platform_supported else 'no'}\n"
                f"Feature flag enabled: {'yes' if guard_lookup.get('feature_flag_enabled') else 'no'}\n"
                f"Demo safe mode disabled: {'yes' if guard_lookup.get('app_demo_safe_mode_disabled') else 'no'}\n"
                f"Real shutdown enabled: {'yes' if guard_lookup.get('real_shutdown_enabled') else 'no'}\n"
                f"Real command enabled: {'yes' if guard_lookup.get('real_command_enabled') else 'no'}\n"
                f"Confirmation required: {'yes' if guard_lookup.get('manual_confirmation_required') else 'no'}\n"
                f"Confirmation phrase required: {'yes' if guard_lookup.get('confirmation_phrase_required') else 'no'}\n"
                f"Countdown seconds: {self.config.get('shutdown', {}).get('real_shutdown_countdown_seconds', 60)}\n"
                f"Abort available: {'yes' if guard_lookup.get('abort_enabled') else 'no'}\n"
                f"Message: {guard_report.message}"
            )
        )

    def check_real_shutdown_guards(self) -> None:
        result = self.manager.check_real_shutdown_guards()
        self._display_result("check_real_shutdown_guards", result)
        self.refresh_status()

    def request_guarded_real_shutdown(self) -> None:
        phrase = self.confirmation_entry.get()
        result = self.manager.request_guarded_real_shutdown(phrase)
        self.confirmation_entry.delete(0, "end")
        self._display_result("request_guarded_real_shutdown", result)
        self.refresh_status()

    def abort_pending_real_shutdown(self) -> None:
        result = self.manager.abort_pending_real_shutdown()
        self._display_result("abort_pending_real_shutdown", result)
        self.refresh_status()

    def _schedule_countdown_tick(self) -> None:
        if self.countdown_after_id is not None:
            return
        self.countdown_after_id = self.after(1000, self._run_countdown_tick)

    def _run_countdown_tick(self) -> None:
        self.countdown_after_id = None
        result = self.manager.perform_action("tick_demo_countdown")
        self._display_result("tick_demo_countdown", result)
        self.refresh_status()
        if result.success and result.state.countdown_running:
            self._schedule_countdown_tick()

    def _cancel_countdown_timer(self) -> None:
        if self.countdown_after_id is not None:
            try:
                self.after_cancel(self.countdown_after_id)
            except Exception:
                pass
            self.countdown_after_id = None

    def _display_result(self, action: str, result: ShutdownEscalationActionResult) -> None:
        message = result.message
        if action == "tick_demo_countdown" and result.state.countdown_running:
            message = "Demo shutdown countdown running. No shutdown will be performed."
        self.message_banner.set_message(message)
        self.result_label.configure(
            text=(
                f"Last shutdown dry-run action: {action}\n"
                f"Status: {result.status}\n"
                f"Previous mode: {result.previous_mode}\n"
                f"New mode: {result.new_mode}\n"
                f"Shutdown candidate: {'yes' if result.state.shutdown_candidate else 'no'}\n"
                f"Countdown running: {'yes' if result.state.countdown_running else 'no'}\n"
                f"Countdown remaining: {result.state.countdown_remaining_seconds}s\n"
                f"Threat level: {result.state.threat_level_at_last_update}\n"
                f"Protected mode: {result.state.protected_mode_at_last_update}\n"
                f"Protected shutdown candidate: {'yes' if result.state.protected_shutdown_candidate else 'no'}\n"
                f"Guarded real shutdown ready: {'yes' if result.state.guarded_real_shutdown_ready else 'no'}\n"
                f"Real shutdown requested: {'yes' if result.state.real_shutdown_requested else 'no'}\n"
                f"Real shutdown scheduled: {'yes' if result.state.real_shutdown_scheduled else 'no'}\n"
                f"Real shutdown aborted: {'yes' if result.state.real_shutdown_aborted else 'no'}\n"
                f"Real shutdown result: {result.state.real_shutdown_result_status}\n"
                "Shutdown performed: no\n"
                "Restart performed: no\n"
                "Lockdown performed: no\n"
                "Alarm performed: no\n"
                "Email sent: no"
            )
        )

    def release_resources(self) -> None:
        self._cancel_countdown_timer()

    def destroy(self) -> None:
        self.release_resources()
        super().destroy()

"""Protected mode demo foundation screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.protected_mode import ProtectedModeActionResult, ProtectedModeManager


class ProtectedModePreviewScreen(ctk.CTkFrame):
    """Manual protected-mode foundation simulator with no enforcement."""

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.config = context.load_result.config
        self.manager = ProtectedModeManager(self.config)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=1)

        PageHeader(
            page,
            "Protected Mode Demo",
            "Model future protected-mode states locally without locking, blocking input, sending alerts, or shutting down.",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 10))

        InfoBanner(
            page,
            "Foundation demo only. No protected enforcement, keyboard/mouse blocking, fullscreen lock, shutdown, lockdown, alarm, "
            "automatic email, camera monitoring, or background surveillance runs here.",
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
            text="Protected State",
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
            text="Last protected-mode action: not run yet",
            justify="left",
            anchor="w",
            text_color=ds.TEXT_PRIMARY,
            wraplength=390,
            font=ctk.CTkFont(size=ds.FONT_SMALL),
        )
        self.result_label.grid(row=0, column=0, sticky="ew", padx=ds.SPACE_MD, pady=ds.SPACE_SM)

        self.message_banner = InfoBanner(
            left_panel,
            "Use manual buttons to model protected-mode states. Real enforcement is not connected.",
            kind="neutral",
            compact=True,
            wraplength=390,
        )
        self.message_banner.grid(row=3, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))

        ctk.CTkLabel(
            right_panel,
            text="Manual Actions",
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))

        button_grid = ctk.CTkFrame(right_panel, fg_color="transparent")
        button_grid.grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_MD))
        for column in (0, 1):
            button_grid.grid_columnconfigure(column, weight=1)

        buttons = (
            ("Arm Protected Mode", "arm", 0, 0),
            ("Activate Demo Protected Mode", "activate_demo", 0, 1),
            ("Mark Recovery Required", "mark_recovery_required", 1, 0),
            ("Simulate Recovery Success", "simulate_recovery_success", 1, 1),
            ("Simulate Recovery Failure", "simulate_recovery_failure", 2, 0),
            ("Apply Current Threat Recommendation", "apply_threat_recommendation", 2, 1),
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
        ctk.CTkButton(utility_row, text="Reset Protected Mode", command=lambda: self.perform_action("reset"), **ds.secondary_button_kwargs()).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        ctk.CTkButton(utility_row, text="Refresh Status", command=self.refresh_status, **ds.secondary_button_kwargs()).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        self.refresh_status()

    def perform_action(self, action: str) -> None:
        result = self.manager.perform_action(action)
        self._display_result(action, result)
        self.refresh_status()

    def refresh_status(self) -> None:
        status = self.manager.build_status()
        state = status.state
        self.status_label.configure(
            text=(
                f"Current mode: {state.mode}\n"
                f"Armed: {'yes' if state.armed else 'no'}\n"
                f"Active demo: {'yes' if state.active_demo else 'no'}\n"
                f"Recovery required: {'yes' if state.recovery_required else 'no'}\n"
                f"Current threat level: {status.threat_level}\n"
                f"Threat recommendation: {status.threat_recommendation}\n"
                f"Shutdown candidate: {'yes' if state.shutdown_candidate else 'no'}\n"
                "Lockdown performed: no\n"
                "Shutdown performed: no\n"
                f"Demo-only mode: {'yes' if status.demo_only else 'review required'}\n"
                "Final enforcement: not connected"
            )
        )

    def _display_result(self, action: str, result: ProtectedModeActionResult) -> None:
        self.message_banner.set_message(result.message)
        self.result_label.configure(
            text=(
                f"Last protected-mode action: {action}\n"
                f"Status: {result.status}\n"
                f"Previous mode: {result.previous_mode}\n"
                f"New mode: {result.new_mode}\n"
                f"Armed: {'yes' if result.state.armed else 'no'}\n"
                f"Active demo: {'yes' if result.state.active_demo else 'no'}\n"
                f"Recovery required: {'yes' if result.state.recovery_required else 'no'}\n"
                f"Shutdown candidate: {'yes' if result.state.shutdown_candidate else 'no'}\n"
                "Lockdown performed: no\n"
                "Shutdown performed: no"
            )
        )

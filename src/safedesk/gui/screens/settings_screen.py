"""Whitelisted owner settings for SafeDesk local preferences."""

from __future__ import annotations

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.developer_tools import DeveloperToolsPolicy
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.logging.event_logger import build_logger_from_config
from safedesk.settings import ManagedSettingsSnapshot, SettingsService


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.config = context.load_result.config
        self.service = SettingsService(
            self.config,
            context.env,
            configuration_valid=context.report.is_valid,
            root=context.project_root,
        )
        self.developer_tools_status = DeveloperToolsPolicy(
            self.config,
            effective_environment=context.settings.environment,
        ).build_status()
        self.event_logger = build_logger_from_config(self.config)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        page = ScrollablePage(self, mousewheel_units=6)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)

        PageHeader(
            page,
            "Settings",
            "Approved local preferences for the authenticated SafeDesk owner.",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, ds.SPACE_MD))
        InfoBanner(
            page,
            "Changes are saved only to ignored local configuration and require a SafeDesk restart. Security credentials and unfinished real-security controls are not editable here.",
            kind="info",
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, ds.SPACE_MD))

        self.variables = self._build_variables(self.service.current_snapshot())
        self.volume_value_label: ctk.CTkLabel | None = None
        self.developer_status_labels: dict[str, ctk.CTkLabel] = {}
        self.developer_guidance_label: ctk.CTkLabel | None = None
        form = ctk.CTkFrame(page, fg_color="transparent")
        form.grid(row=2, column=0, sticky="ew")
        form.grid_columnconfigure((0, 1), weight=1, uniform="settings_columns")

        self._application_section(form).grid(row=0, column=0, sticky="nsew", padx=(4, ds.SPACE_SM), pady=ds.SPACE_SM)
        self._tray_section(form).grid(row=0, column=1, sticky="nsew", padx=(ds.SPACE_SM, 4), pady=ds.SPACE_SM)
        self._shortcut_section(form).grid(row=1, column=0, sticky="nsew", padx=(4, ds.SPACE_SM), pady=ds.SPACE_SM)
        self._logging_section(form).grid(row=1, column=1, sticky="nsew", padx=(ds.SPACE_SM, 4), pady=ds.SPACE_SM)
        self._alarm_section(form).grid(row=2, column=0, sticky="nsew", padx=(4, ds.SPACE_SM), pady=ds.SPACE_SM)
        self._developer_section(form).grid(row=2, column=1, sticky="nsew", padx=(ds.SPACE_SM, 4), pady=ds.SPACE_SM)

        actions = ctk.CTkFrame(page, **ds.card_kwargs())
        actions.grid(row=3, column=0, sticky="ew", padx=4, pady=(ds.SPACE_MD, ds.SPACE_SM))
        actions.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkButton(actions, text="Save Settings", command=self._save, **ds.primary_button_kwargs()).grid(
            row=0, column=0, sticky="ew", padx=(ds.SPACE_LG, ds.SPACE_SM), pady=ds.SPACE_LG
        )
        ctk.CTkButton(actions, text="Restore Safe Defaults", command=self._show_restore_confirmation, **ds.secondary_button_kwargs()).grid(
            row=0, column=1, sticky="ew", padx=ds.SPACE_SM, pady=ds.SPACE_LG
        )
        ctk.CTkButton(actions, text="Reload Startup Values", command=self._reload, **ds.secondary_button_kwargs()).grid(
            row=0, column=2, sticky="ew", padx=(ds.SPACE_SM, ds.SPACE_LG), pady=ds.SPACE_LG
        )

        self.restore_confirmation = ctk.CTkFrame(page, **ds.panel_kwargs())
        self.restore_confirmation.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(
            self.restore_confirmation,
            text="Restore only Settings-managed preferences to safe defaults? Unrelated local configuration and runtime data will be preserved.",
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=820,
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))
        ctk.CTkButton(self.restore_confirmation, text="Confirm Restore", command=self._confirm_restore, **ds.primary_button_kwargs()).grid(
            row=1, column=0, sticky="ew", padx=(ds.SPACE_LG, ds.SPACE_SM), pady=(0, ds.SPACE_LG)
        )
        ctk.CTkButton(self.restore_confirmation, text="Cancel", command=self._cancel_restore, **ds.secondary_button_kwargs()).grid(
            row=1, column=1, sticky="ew", padx=(ds.SPACE_SM, ds.SPACE_LG), pady=(0, ds.SPACE_LG)
        )
        self.restore_confirmation.grid(row=4, column=0, sticky="ew", padx=4, pady=ds.SPACE_SM)
        self.restore_confirmation.grid_remove()

        self.message_banner = InfoBanner(page, self.service.build_status().message, kind="neutral")
        self.message_banner.grid(row=5, column=0, sticky="ew", padx=4, pady=(ds.SPACE_SM, ds.SPACE_LG))
        page.bind_descendants_for_scroll()
        self._log_event("settings_opened", "Settings opened.", {"result_status": "opened"})

    def _application_section(self, master):
        frame = self._section(master, "Application")
        self._switch(frame, 1, "Start maximized", "start_maximized")
        return frame

    def _tray_section(self, master):
        frame = self._section(master, "Tray and Background")
        self._switch(frame, 1, "Minimize to tray", "minimize_to_tray")
        self._switch(frame, 2, "Close to tray", "close_to_tray")
        self._switch(frame, 3, "Allow Exit from tray", "allow_exit_from_tray")
        self._read_only(frame, 4, "Tray foundation", self._enabled(self.config.get("background_agent", {}).get("foundation_enabled")))
        return frame

    def _shortcut_section(self, master):
        frame = self._section(master, "Global Shortcut")
        self._switch(frame, 1, "Enable global shortcut", "global_shortcut_enabled")
        self._read_only(frame, 2, "Shortcut", "Ctrl + Alt + L")
        self._read_only(frame, 3, "Application", "Restart required")
        return frame

    def _logging_section(self, master):
        frame = self._section(master, "Event Logging")
        self._entry(frame, 1, "Maximum recent events", "max_recent_events")
        self._entry(frame, 2, "Retention days", "retention_days")
        return frame

    def _alarm_section(self, master):
        frame = self._section(master, "Alarm Preview")
        self._switch(frame, 1, "Enable manual preview", "manual_alarm_preview_enabled")
        self._entry(frame, 2, "Maximum duration (seconds)", "alarm_preview_duration_seconds")
        self._switch(frame, 3, "Enable beep fallback", "alarm_beep_fallback_enabled")
        ctk.CTkLabel(frame, text="Advisory volume", text_color=ds.TEXT_MUTED, anchor="w").grid(
            row=4, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_SM, 0)
        )
        slider = ctk.CTkSlider(
            frame,
            from_=0.0,
            to=1.0,
            number_of_steps=20,
            variable=self.variables["alarm_advisory_volume"],
            command=self._volume_changed,
        )
        slider.grid(row=5, column=0, sticky="ew", padx=ds.SPACE_LG, pady=ds.SPACE_SM)
        self.volume_value_label = ctk.CTkLabel(frame, text="", text_color=ds.TEXT_SECONDARY, anchor="w")
        self.volume_value_label.grid(row=6, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))
        self._volume_changed(self.variables["alarm_advisory_volume"].get())
        self._read_only(frame, 7, "Automatic alarm triggers", "disabled")
        return frame

    def _developer_section(self, master):
        frame = self._section(master, "Developer Tools")
        ctk.CTkLabel(
            frame,
            text=(
                "There is no separate Developer Mode switch. Enable at least one visibility option, save, and restart. "
                "Developer Tools appears under Developer only when every safe runtime policy guard passes."
            ),
            text_color=ds.TEXT_SECONDARY,
            anchor="w",
            justify="left",
            wraplength=420,
        ).grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_SM))
        self._switch(frame, 2, "Show demo screens", "show_demo_screens", command=self._refresh_developer_status)
        self._switch(
            frame,
            3,
            "Show safe runtime diagnostics",
            "show_runtime_diagnostics",
            command=self._refresh_developer_status,
        )
        status = self.developer_tools_status
        self.developer_status_labels["eligibility"] = self._read_only(frame, 4, "Developer Tools eligibility", "")
        self.developer_status_labels["environment"] = self._read_only(
            frame,
            5,
            "Effective environment",
            "development" if status.environment_supported else "other",
        )
        self.developer_status_labels["demo_safe"] = self._read_only(
            frame,
            6,
            "Demo-safe mode",
            "enabled" if status.demo_safe_mode else "disabled",
        )
        self.developer_status_labels["security"] = self._read_only(
            frame,
            7,
            "Security mode",
            "demo_safe" if status.security_mode_supported else "other",
        )
        self.developer_status_labels["foundation"] = self._read_only(
            frame,
            8,
            "Foundation",
            "enabled" if status.foundation_enabled else "disabled",
        )
        self.developer_status_labels["demos"] = self._read_only(frame, 9, "Demo screens after restart", "")
        self.developer_status_labels["diagnostics"] = self._read_only(frame, 10, "Diagnostics after restart", "")
        self.developer_guidance_label = ctk.CTkLabel(
            frame,
            text="",
            text_color=ds.TEXT_SECONDARY,
            anchor="w",
            justify="left",
            wraplength=420,
        )
        self.developer_guidance_label.grid(row=11, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_SM, ds.SPACE_LG))
        self._refresh_developer_status()
        return frame

    def _save(self) -> None:
        snapshot = self._snapshot_from_form()
        if snapshot is None:
            return
        self._log_event("settings_save_requested", "Managed settings save was requested.", {"result_status": "requested"})
        result = self.service.save(snapshot)
        action = "settings_saved" if result.success else "settings_save_rejected"
        self._log_event(
            action,
            result.message,
            {
                "changed_setting_count": result.changed_setting_count,
                "restart_required": result.restart_required,
                "result_status": result.status,
                "local_override_present": result.local_override_present,
            },
        )
        self.message_banner.set_message(result.message)

    def _reload(self) -> None:
        self._load_snapshot(self.service.current_snapshot())
        self.message_banner.set_message(
            "Startup-loaded values from the current running session were reloaded. No changes were written."
        )

    def _show_restore_confirmation(self) -> None:
        self.restore_confirmation.grid()
        self._log_event("settings_defaults_restore_requested", "Safe defaults restore was requested.", {"result_status": "confirmation_required"})

    def _cancel_restore(self) -> None:
        self.restore_confirmation.grid_remove()
        self.message_banner.set_message("Restore Safe Defaults was cancelled. No changes were written.")
        self._log_event("settings_defaults_restore_cancelled", "Safe defaults restore was cancelled.", {"result_status": "cancelled"})

    def _confirm_restore(self) -> None:
        result = self.service.restore_defaults()
        self.restore_confirmation.grid_remove()
        self.message_banner.set_message(result.message)
        action = "settings_defaults_restored" if result.success else "settings_save_rejected"
        self._log_event(
            action,
            result.message,
            {
                "changed_setting_count": result.changed_setting_count,
                "restart_required": result.restart_required,
                "result_status": result.status,
                "local_override_present": result.local_override_present,
            },
        )

    def _snapshot_from_form(self) -> ManagedSettingsSnapshot | None:
        try:
            max_recent = int(self.variables["max_recent_events"].get().strip())
        except (TypeError, ValueError):
            self.message_banner.set_message("Maximum recent events must be an integer between 10 and 500.")
            return None
        try:
            retention = int(self.variables["retention_days"].get().strip())
        except (TypeError, ValueError):
            self.message_banner.set_message("Retention days must be an integer between 1 and 3650.")
            return None
        try:
            duration = int(self.variables["alarm_preview_duration_seconds"].get().strip())
        except (TypeError, ValueError):
            self.message_banner.set_message("Alarm preview duration must be an integer between 1 and 10.")
            return None

        return ManagedSettingsSnapshot(
            start_maximized=self.variables["start_maximized"].get(),
            minimize_to_tray=self.variables["minimize_to_tray"].get(),
            close_to_tray=self.variables["close_to_tray"].get(),
            allow_exit_from_tray=self.variables["allow_exit_from_tray"].get(),
            global_shortcut_enabled=self.variables["global_shortcut_enabled"].get(),
            max_recent_events=max_recent,
            retention_days=retention,
            manual_alarm_preview_enabled=self.variables["manual_alarm_preview_enabled"].get(),
            alarm_preview_duration_seconds=duration,
            alarm_beep_fallback_enabled=self.variables["alarm_beep_fallback_enabled"].get(),
            alarm_advisory_volume=float(self.variables["alarm_advisory_volume"].get()),
            show_demo_screens=self.variables["show_demo_screens"].get(),
            show_runtime_diagnostics=self.variables["show_runtime_diagnostics"].get(),
        )

    def _load_snapshot(self, snapshot: ManagedSettingsSnapshot) -> None:
        for name, value in snapshot.__dict__.items():
            variable = self.variables.get(name)
            if variable is not None:
                variable.set(value)
        self._volume_changed(snapshot.alarm_advisory_volume)
        self._refresh_developer_status()

    @staticmethod
    def _build_variables(snapshot: ManagedSettingsSnapshot) -> dict:
        return {
            "start_maximized": ctk.BooleanVar(value=snapshot.start_maximized),
            "minimize_to_tray": ctk.BooleanVar(value=snapshot.minimize_to_tray),
            "close_to_tray": ctk.BooleanVar(value=snapshot.close_to_tray),
            "allow_exit_from_tray": ctk.BooleanVar(value=snapshot.allow_exit_from_tray),
            "global_shortcut_enabled": ctk.BooleanVar(value=snapshot.global_shortcut_enabled),
            "max_recent_events": ctk.StringVar(value=str(snapshot.max_recent_events)),
            "retention_days": ctk.StringVar(value=str(snapshot.retention_days)),
            "manual_alarm_preview_enabled": ctk.BooleanVar(value=snapshot.manual_alarm_preview_enabled),
            "alarm_preview_duration_seconds": ctk.StringVar(value=str(snapshot.alarm_preview_duration_seconds)),
            "alarm_beep_fallback_enabled": ctk.BooleanVar(value=snapshot.alarm_beep_fallback_enabled),
            "alarm_advisory_volume": ctk.DoubleVar(value=snapshot.alarm_advisory_volume),
            "show_demo_screens": ctk.BooleanVar(value=snapshot.show_demo_screens),
            "show_runtime_diagnostics": ctk.BooleanVar(value=snapshot.show_runtime_diagnostics),
        }

    @staticmethod
    def _section(master, title: str):
        frame = ctk.CTkFrame(master, **ds.card_kwargs())
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame,
            text=title,
            text_color=ds.TEXT_PRIMARY,
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))
        return frame

    def _switch(self, frame, row: int, text: str, variable_name: str, command=None) -> None:
        ctk.CTkSwitch(
            frame,
            text=text,
            variable=self.variables[variable_name],
            text_color=ds.TEXT_PRIMARY,
            command=command,
        ).grid(row=row, column=0, sticky="w", padx=ds.SPACE_LG, pady=ds.SPACE_SM)

    def _entry(self, frame, row: int, label: str, variable_name: str) -> None:
        host = ctk.CTkFrame(frame, fg_color="transparent")
        host.grid(row=row, column=0, sticky="ew", padx=ds.SPACE_LG, pady=ds.SPACE_SM)
        host.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(host, text=label, text_color=ds.TEXT_MUTED, anchor="w").grid(row=0, column=0, sticky="ew")
        ctk.CTkEntry(host, textvariable=self.variables[variable_name], width=120).grid(row=1, column=0, sticky="w", pady=(ds.SPACE_XS, 0))

    @staticmethod
    def _read_only(frame, row: int, label: str, value: str):
        host = ctk.CTkFrame(frame, fg_color="transparent")
        host.grid(row=row, column=0, sticky="ew", padx=ds.SPACE_LG, pady=ds.SPACE_SM)
        host.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(host, text=label, text_color=ds.TEXT_MUTED, anchor="w").grid(row=0, column=0, sticky="w")
        value_label = ctk.CTkLabel(host, text=value, text_color=ds.TEXT_PRIMARY, anchor="e")
        value_label.grid(row=0, column=1, sticky="e")
        return value_label

    def _refresh_developer_status(self) -> None:
        if not self.developer_status_labels:
            return
        status = self.developer_tools_status
        guards_pass = all(
            (
                status.environment_supported,
                status.demo_safe_mode,
                status.security_mode_supported,
                status.foundation_enabled,
                status.demo_only,
            )
        )
        show_demos = bool(self.variables["show_demo_screens"].get())
        show_diagnostics = bool(self.variables["show_runtime_diagnostics"].get())
        self.developer_status_labels["eligibility"].configure(text="available" if guards_pass else "unavailable")
        self.developer_status_labels["demos"].configure(text="visible" if guards_pass and show_demos else "hidden")
        self.developer_status_labels["diagnostics"].configure(
            text="visible" if guards_pass and show_diagnostics else "hidden"
        )
        if not guards_pass:
            message = "Developer Tools are unavailable under the current safe runtime policy."
        elif not (show_demos or show_diagnostics):
            message = "Enable demo screens or diagnostics, save, and restart SafeDesk."
        else:
            message = "Developer Tools will be available from the Developer section after restart."
        if self.developer_guidance_label is not None:
            self.developer_guidance_label.configure(text=message)

    def _volume_changed(self, value) -> None:
        if self.volume_value_label is not None:
            self.volume_value_label.configure(text=f"{float(value):.2f} advisory only")

    def _log_event(self, action: str, message: str, metadata: dict) -> None:
        try:
            self.event_logger.log_app_event(action=action, status="info", message=message, metadata=metadata)
        except Exception:
            pass

    @staticmethod
    def _enabled(value) -> str:
        return "enabled" if value is True else "disabled"

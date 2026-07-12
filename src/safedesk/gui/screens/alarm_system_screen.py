"""Owner-only SafeDesk alarm preview screen."""

from __future__ import annotations

import customtkinter as ctk

from safedesk.alarm import AlarmPreviewStatus, SafeAlarmPreviewManager
from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.gui.components.status_card import StatusCard
from safedesk.logging.event_logger import build_logger_from_config


class AlarmSystemScreen(ctk.CTkFrame):
    """Manual, short, stoppable alarm preview controls for the authenticated owner."""

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.config = context.load_result.config
        self.event_logger = build_logger_from_config(self.config)
        self.manager = SafeAlarmPreviewManager(self.config, event_callback=self._log_preview_event)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self, mousewheel_units=5)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)

        PageHeader(
            page,
            "Alarm System",
            "Owner-controlled demo-safe local alarm preview.",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, ds.SPACE_MD))

        InfoBanner(
            page,
            "Manual preview only. No automatic security trigger is connected. Every preview is short, non-looping, and stoppable.",
            kind="warning",
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, ds.SPACE_MD))

        self.status_card_host = ctk.CTkFrame(page, fg_color="transparent")
        self.status_card_host.grid(row=2, column=0, sticky="ew", padx=4, pady=(0, ds.SPACE_MD))
        self.status_card_host.grid_columnconfigure(0, weight=1)

        controls = ctk.CTkFrame(page, **ds.card_kwargs())
        controls.grid(row=3, column=0, sticky="ew", padx=4, pady=(0, ds.SPACE_MD))
        controls.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            controls,
            text="Manual Preview",
            text_color=ds.TEXT_PRIMARY,
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=3, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, ds.SPACE_SM))

        self.play_button = ctk.CTkButton(
            controls,
            text="Play Safe Preview",
            command=self._play_preview,
            **ds.primary_button_kwargs(),
        )
        self.play_button.grid(row=1, column=0, sticky="ew", padx=(ds.SPACE_LG, ds.SPACE_SM), pady=(0, ds.SPACE_LG))

        self.stop_button = ctk.CTkButton(
            controls,
            text="Stop Preview",
            command=self._stop_preview,
            **ds.secondary_button_kwargs(),
        )
        self.stop_button.grid(row=1, column=1, sticky="ew", padx=ds.SPACE_SM, pady=(0, ds.SPACE_LG))

        self.refresh_button = ctk.CTkButton(
            controls,
            text="Refresh Status",
            command=self.refresh_status,
            **ds.secondary_button_kwargs(),
        )
        self.refresh_button.grid(row=1, column=2, sticky="ew", padx=(ds.SPACE_SM, ds.SPACE_LG), pady=(0, ds.SPACE_LG))

        self.message_banner = InfoBanner(page, "Alarm preview is idle.", kind="info")
        self.message_banner.grid(row=4, column=0, sticky="ew", padx=4, pady=(0, ds.SPACE_MD))

        ctk.CTkLabel(
            page,
            text="The configured volume is advisory. SafeDesk does not change the operating-system volume or mixer.",
            text_color=ds.TEXT_MUTED,
            font=ctk.CTkFont(size=ds.FONT_SMALL),
            anchor="w",
            justify="left",
            wraplength=860,
        ).grid(row=5, column=0, sticky="ew", padx=8, pady=(0, ds.SPACE_LG))

        self.refresh_status()
        page.bind_descendants_for_scroll()

    def refresh_status(self) -> None:
        """Refresh read-only preview readiness without playing sound."""

        status = self.manager.build_status()
        for child in self.status_card_host.winfo_children():
            child.destroy()
        StatusCard(
            self.status_card_host,
            "Preview Status",
            self._status_rows(status),
            accent=ds.SAFEDESK_NEUTRAL,
        ).grid(row=0, column=0, sticky="ew")

        safe_config = (
            status.foundation_enabled
            and status.demo_only
            and status.manual_preview_enabled
            and not status.automatic_trigger_enabled
            and not status.allow_looping
        )
        preview_source_available = status.audio_available or status.beep_fallback_enabled
        can_play = safe_config and status.backend_available and preview_source_available and not status.preview_active
        self.play_button.configure(state="normal" if can_play else "disabled")
        self.stop_button.configure(state="normal" if status.preview_active else "disabled")

    def _play_preview(self) -> None:
        result = self.manager.start_preview(self)
        self.message_banner.set_message(result.message)
        self.refresh_status()

    def _stop_preview(self) -> None:
        result = self.manager.stop_preview(reason="manual")
        self.message_banner.set_message(result.message)
        self.refresh_status()

    def release_resources(self) -> None:
        result = self.manager.release_resources()
        try:
            self.message_banner.set_message(result.message)
            self.refresh_status()
        except Exception:
            pass

    def _log_preview_event(self, action: str, message: str, metadata: dict) -> None:
        try:
            self.event_logger.log_app_event(
                action=action,
                status="info",
                message=message,
                metadata=metadata,
            )
        except Exception:
            pass
        if action == "alarm_preview_timed_out":
            try:
                self.message_banner.set_message(message)
                self.refresh_status()
            except Exception:
                pass

    @staticmethod
    def _status_rows(status: AlarmPreviewStatus) -> list[tuple[str, str]]:
        return [
            ("Real/automatic alarm", "disabled" if not status.enabled else "enabled"),
            ("Foundation", "enabled" if status.foundation_enabled else "disabled"),
            ("Demo-only", "yes" if status.demo_only else "no"),
            ("Manual preview", "enabled" if status.manual_preview_enabled else "disabled"),
            ("Automatic trigger", "enabled" if status.automatic_trigger_enabled else "disabled"),
            ("Looping", "enabled" if status.allow_looping else "disabled"),
            ("Audio file", "configured" if status.audio_configured else "not configured"),
            (
                "Audio availability",
                "available" if status.audio_available else ("unavailable" if status.audio_configured else "not configured"),
            ),
            ("Beep fallback", "enabled" if status.beep_fallback_enabled else "disabled"),
            ("Maximum duration", f"{status.max_preview_duration_seconds} seconds"),
            ("Configured volume", f"{status.configured_volume:.1f} (advisory)"),
            ("Backend", "available" if status.backend_available else "unavailable"),
            ("Preview", "active" if status.preview_active else "idle"),
        ]

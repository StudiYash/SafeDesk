"""Main SafeDesk GUI shell window."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from safedesk.admin_gate import AdminGateManager
from safedesk.app.application import RuntimeContext
from safedesk.app_modes import (
    AppModeManager,
    SafeDeskMode,
    can_open_public_lock_placeholder,
    parse_app_mode,
)
from safedesk.background_agent import BackgroundAgentManager, TrayController
from safedesk.developer_tools import DeveloperToolsPolicy
from safedesk.global_shortcut import GlobalShortcutManager, WindowsHotkeyController
from safedesk.gui import design_system as ds
from safedesk.gui.components.sidebar_button import SidebarButton
from safedesk.gui.navigation import (
    ABOUT,
    ALARM_SYSTEM,
    AUTHENTICATION_SETUP,
    DASHBOARD,
    DEVELOPER_TOOLS,
    EVENT_LOGS,
    FACE_RECOGNITION_DEMO,
    HOME,
    INTRUDER_DETECTION_DEMO,
    INTRUDER_HISTORY,
    LIVENESS_DEMO,
    OWNER_FACE_REGISTRATION,
    OTP_EMAIL_SETUP,
    PROTECTED_MODE_PREVIEW,
    SCREEN_NAMES,
    SETUP_STATUS,
    SETUP_WIZARD,
    SETTINGS,
    SHUTDOWN_ESCALATION,
    THREAT_LEVEL_DEMO,
    admin_route_allowed,
    visible_sidebar_sections,
)
from safedesk.gui.screens.about_screen import AboutScreen
from safedesk.gui.screens.admin_gate_screen import AdminGateScreen
from safedesk.gui.screens.alarm_system_screen import AlarmSystemScreen
from safedesk.gui.screens.authentication_setup_screen import AuthenticationSetupScreen
from safedesk.gui.screens.dashboard_placeholder_screen import DashboardPlaceholderScreen
from safedesk.gui.screens.developer_tools_screen import DeveloperToolsScreen
from safedesk.gui.screens.face_recognition_demo_screen import FaceRecognitionDemoScreen
from safedesk.gui.screens.home_screen import HomeScreen
from safedesk.gui.screens.intruder_detection_demo_screen import IntruderDetectionDemoScreen
from safedesk.gui.screens.intruder_history_screen import IntruderHistoryScreen
from safedesk.gui.screens.launch_screen import LaunchScreen
from safedesk.gui.screens.liveness_demo_screen import LivenessDemoScreen
from safedesk.gui.screens.logging_dashboard_screen import LoggingDashboardScreen
from safedesk.gui.screens.owner_face_registration_screen import OwnerFaceRegistrationScreen
from safedesk.gui.screens.otp_email_setup_screen import OtpEmailSetupScreen
from safedesk.gui.screens.protected_mode_preview_screen import ProtectedModePreviewScreen
from safedesk.gui.screens.public_lock_screen import PublicLockScreen
from safedesk.gui.screens.settings_screen import SettingsScreen
from safedesk.gui.screens.setup_status_screen import SetupStatusScreen
from safedesk.gui.screens.setup_wizard_screen import SetupWizardScreen
from safedesk.gui.screens.shutdown_escalation_screen import ShutdownEscalationScreen
from safedesk.gui.screens.threat_level_demo_screen import ThreatLevelDemoScreen
from safedesk.gui.startup_maximize import StartupMaximizeController
from safedesk.gui.theme import apply_theme
from safedesk.interaction_lock import SafeInteractionLockManager
from safedesk.lockdown_display import LockdownDisplayManager
from safedesk.lockdown_display.dpi_awareness import enable_windows_dpi_awareness
from safedesk.logging.event_logger import build_logger_from_config


class SafeDeskMainWindow(ctk.CTk):
    """Safe placeholder desktop shell for SafeDesk."""

    def __init__(self, context: RuntimeContext):
        enable_windows_dpi_awareness()
        self.context = context
        self.project_root = context.project_root
        self.config = context.load_result.config
        self.ui_config = self.config.get("ui", {})
        self.app_mode_config = self.config.get("app_modes", {})
        self.admin_gate_config = self.config.get("admin_gate", {})
        self.effective_environment = context.settings.environment
        self.developer_tools_policy = DeveloperToolsPolicy(
            self.config,
            effective_environment=self.effective_environment,
        )
        self.public_lock_placeholder_allowed = can_open_public_lock_placeholder(self.config)
        self.mode_manager = AppModeManager(self._configured_start_mode())
        self.event_logger = build_logger_from_config(self.config)
        self.admin_gate_manager = AdminGateManager(self.config)
        self.background_agent_manager = BackgroundAgentManager(self.config)
        self.tray_controller: TrayController | None = None
        self.global_shortcut_manager = GlobalShortcutManager(self.config)
        self.global_shortcut_controller: WindowsHotkeyController | None = None
        self.lockdown_display_manager = LockdownDisplayManager(self.config)
        self.safe_interaction_lock_manager = SafeInteractionLockManager(
            self.config,
            window_provider=self.lockdown_display_manager.get_active_windows,
            event_callback=self._log_safe_interaction_lock_event,
        )
        self._hidden_to_tray = False
        self._destroying = False
        self._startup_maximize_requested = self.ui_config.get("start_maximized") is True
        self.startup_maximize_controller: StartupMaximizeController | None = None
        apply_theme(self.ui_config)
        super().__init__()

        width = int(self.ui_config.get("window_width", 1100))
        height = int(self.ui_config.get("window_height", 700))
        min_width = int(self.ui_config.get("minimum_width", 900))
        min_height = int(self.ui_config.get("minimum_height", 600))

        self.title("SafeDesk")
        self.geometry(f"{width}x{height}")
        self.minsize(min_width, min_height)
        self.configure(fg_color=ds.APP_BG)
        self.protocol("WM_DELETE_WINDOW", self._handle_window_close)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=246, corner_radius=0, fg_color=ds.SIDEBAR_BG)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(3, weight=1)

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=ds.CONTENT_BG)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.current_screen: ctk.CTkFrame | None = None
        self.buttons: dict[str, SidebarButton] = {}
        self.lock_button: SidebarButton | None = None
        self.screen_factories: dict[str, Callable[[ctk.CTkFrame, RuntimeContext], ctk.CTkFrame]] = {
            HOME: HomeScreen,
            SETUP_WIZARD: SetupWizardScreen,
            SETUP_STATUS: SetupStatusScreen,
            OWNER_FACE_REGISTRATION: OwnerFaceRegistrationScreen,
            FACE_RECOGNITION_DEMO: FaceRecognitionDemoScreen,
            LIVENESS_DEMO: LivenessDemoScreen,
            AUTHENTICATION_SETUP: AuthenticationSetupScreen,
            OTP_EMAIL_SETUP: OtpEmailSetupScreen,
            EVENT_LOGS: LoggingDashboardScreen,
            INTRUDER_DETECTION_DEMO: IntruderDetectionDemoScreen,
            INTRUDER_HISTORY: IntruderHistoryScreen,
            THREAT_LEVEL_DEMO: ThreatLevelDemoScreen,
            PROTECTED_MODE_PREVIEW: ProtectedModePreviewScreen,
            SHUTDOWN_ESCALATION: ShutdownEscalationScreen,
            ALARM_SYSTEM: AlarmSystemScreen,
            DEVELOPER_TOOLS: lambda master, runtime_context: DeveloperToolsScreen(
                master,
                runtime_context,
                on_open_screen=self.show_screen,
            ),
            DASHBOARD: DashboardPlaceholderScreen,
            SETTINGS: SettingsScreen,
            ABOUT: AboutScreen,
        }

        self._build_sidebar()
        self._start_background_agent_if_configured()
        self._start_global_shortcut_if_configured()
        self._show_initial_mode()
        self.startup_maximize_controller = StartupMaximizeController(
            self,
            requested=self._startup_maximize_requested,
            destroying=lambda: self._destroying,
        )
        self.startup_maximize_controller.arm()

    def _build_sidebar(self) -> None:
        title = ctk.CTkLabel(
            self.sidebar,
            text="SafeDesk",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
            anchor="w",
        )
        title.grid(row=0, column=0, padx=20, pady=(24, 4), sticky="ew")

        subtitle = ctk.CTkLabel(
            self.sidebar,
            text="Owner-controlled security",
            font=ctk.CTkFont(size=12),
            text_color=ds.TEXT_MUTED,
            anchor="w",
        )
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 12), sticky="ew")

        mode = self.context.settings.security_mode
        safe_mode = "Demo/safe mode enabled" if self.context.settings.demo_safe_mode else "Demo/safe mode disabled"
        status = ctk.CTkFrame(
            self.sidebar,
            fg_color=ds.CARD_BG,
            corner_radius=ds.RADIUS_MD,
            border_width=1,
            border_color=ds.BORDER_MUTED,
        )
        status.grid(row=2, column=0, padx=16, pady=(0, 18), sticky="ew")
        status.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            status,
            text=mode,
            text_color=ds.TEXT_PRIMARY,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=12, pady=(10, 2), sticky="ew")
        ctk.CTkLabel(
            status,
            text=safe_mode,
            text_color=ds.TEXT_SECONDARY,
            font=ctk.CTkFont(size=11),
            anchor="w",
        ).grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.nav_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color=ds.SIDEBAR_BG,
            corner_radius=0,
            scrollbar_button_color=ds.BORDER_MUTED,
            scrollbar_button_hover_color=ds.SAFEDESK_RED,
        )
        self.nav_frame.grid(row=3, column=0, sticky="nsew", padx=0, pady=(0, 12))
        self.nav_frame.grid_columnconfigure(0, weight=1)

        row_index = 0
        for section_name, screens in visible_sidebar_sections(
            self.config,
            effective_environment=self.effective_environment,
        ):
            ctk.CTkLabel(
                self.nav_frame,
                text=section_name,
                text_color=ds.TEXT_MUTED,
                font=ctk.CTkFont(size=11, weight="bold"),
                anchor="w",
            ).grid(row=row_index, column=0, padx=20, pady=(12, 4), sticky="ew")
            row_index += 1
            for screen in screens:
                button = SidebarButton(
                    self.nav_frame,
                    text=screen.label,
                    command=lambda name=screen.name: self.show_screen(name),
                )
                button.grid(row=row_index, column=0, padx=14, pady=4, sticky="ew")
                self.buttons[screen.name] = button
                row_index += 1

        self.lock_button = SidebarButton(self.sidebar, text="Lock SafeDesk", command=self.show_public_lock_screen)
        if not self.public_lock_placeholder_allowed:
            self.lock_button.configure(state="disabled")
        self.lock_button.grid(row=4, column=0, padx=14, pady=(0, 16), sticky="ew")

    def _configured_start_mode(self) -> SafeDeskMode:
        configured = parse_app_mode(self.app_mode_config.get("default_start_mode", SafeDeskMode.LAUNCH.value))
        if configured == SafeDeskMode.PUBLIC_LOCK and not self.public_lock_placeholder_allowed:
            return SafeDeskMode.LAUNCH
        if configured in {SafeDeskMode.ADMIN_GATE, SafeDeskMode.ADMIN_CONSOLE, SafeDeskMode.PUBLIC_LOCK}:
            return configured
        return SafeDeskMode.LAUNCH

    def _show_initial_mode(self) -> None:
        initial_mode = self.mode_manager.current_mode
        if initial_mode in {SafeDeskMode.ADMIN_GATE, SafeDeskMode.ADMIN_CONSOLE}:
            self.show_admin_gate()
        elif initial_mode == SafeDeskMode.PUBLIC_LOCK:
            self.show_public_lock_screen()
        else:
            self.show_launch_screen()

    def _clear_current_screen(self) -> None:
        if self.current_screen is not None:
            self._release_current_screen_resources()
            self.current_screen.destroy()
            self.current_screen = None

    def _show_admin_layout(self) -> None:
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.content.grid_configure(row=0, column=1, columnspan=1, sticky="nsew")

    def _show_route_layout(self) -> None:
        self.sidebar.grid_remove()
        self.content.grid_configure(row=0, column=0, columnspan=2, sticky="nsew")

    def _log_app_route_event(self, action: str, message: str, metadata: dict | None = None) -> None:
        try:
            event_metadata = {"mode": self.mode_manager.current_mode.value}
            if metadata:
                event_metadata.update(metadata)
            self.event_logger.log_app_event(action=action, status="info", message=message, metadata=event_metadata)
        except Exception:
            pass

    def _log_safe_interaction_lock_event(self, action: str, message: str, metadata: dict) -> None:
        self._log_app_route_event(action, message, metadata)

    def _start_background_agent_if_configured(self) -> None:
        if not self.background_agent_manager.should_attempt_tray():
            return

        self.tray_controller = TrayController(
            dispatch_to_gui=self._dispatch_gui_action_from_tray,
            on_open_safedesk=self.show_launch_screen_from_tray,
            on_open_admin_console=self.show_admin_gate_from_tray,
            on_lock_safedesk=self.show_public_lock_from_tray,
            on_exit_safedesk=self.exit_from_tray,
            allow_exit=self.background_agent_manager.allow_exit_from_tray,
        )
        result = self.tray_controller.start()
        if result.success:
            self._log_app_route_event(
                "tray_icon_started",
                "SafeDesk system tray support started.",
                {"tray_available": result.tray_available, "tray_running": result.tray_running},
            )
        else:
            self._log_app_route_event(
                "tray_icon_unavailable",
                "SafeDesk system tray support is unavailable.",
                {"tray_available": False, "tray_running": False},
            )

    def _start_lockdown_display(self) -> None:
        self._log_app_route_event(
            "public_lock_fullscreen_requested",
            "Fullscreen SafeDesk lockdown display was requested.",
            {
                "route": SafeDeskMode.PUBLIC_LOCK.value,
                "current_mode": self.mode_manager.current_mode.value,
                "fullscreen_enabled": self.lockdown_display_manager.fullscreen_enabled,
                "multi_display_enabled": self.lockdown_display_manager.multi_display_enabled,
            },
        )
        result = self.lockdown_display_manager.start(
            self,
            self.context,
            on_development_escape=self._handle_lockdown_development_escape,
        )
        metadata = {
            "display_count": result.display_count,
            "window_count": result.window_count,
            "fullscreen_enabled": self.lockdown_display_manager.fullscreen_enabled,
            "multi_display_enabled": self.lockdown_display_manager.multi_display_enabled,
            "fallback_used": result.fallback_used,
            "active": self.lockdown_display_manager.active,
            "result_status": result.status,
        }
        if result.status == "already_active":
            self._log_app_route_event("lockdown_display_already_active", "Lockdown display is already active.", metadata)
        elif result.success:
            if result.fallback_used:
                self._log_app_route_event("lockdown_display_primary_fallback_used", "Primary display fallback was used.", metadata)
            self._log_app_route_event("lockdown_display_started", "Lockdown display windows started.", metadata)
        else:
            self._log_app_route_event("lockdown_display_unavailable", "Lockdown display windows are unavailable.", metadata)

        if result.success and self.lockdown_display_manager.active:
            self._start_safe_interaction_lock()

    def _start_safe_interaction_lock(self) -> None:
        result = self.safe_interaction_lock_manager.start(
            self,
            window_provider=self.lockdown_display_manager.get_active_windows,
        )
        if not result.success or not self.safe_interaction_lock_manager.active:
            return
        focus_primary = self.safe_interaction_lock_manager.focus_primary_on_activation
        self._log_app_route_event(
            "lockdown_visual_recovery_requested",
            "SafeDesk lockdown visual recovery was requested.",
            {
                "window_count": result.window_count,
                "focus_primary": focus_primary,
                "result_status": result.status,
            },
        )
        self.safe_interaction_lock_manager.recover_once(focus_primary=focus_primary)

    def _stop_safe_interaction_lock(self) -> None:
        if self.safe_interaction_lock_manager.active:
            self.safe_interaction_lock_manager.stop()

    def _stop_lockdown_display(self) -> None:
        self._stop_safe_interaction_lock()
        if not self.lockdown_display_manager.active:
            return
        status = self.lockdown_display_manager.build_status()
        self._log_app_route_event(
            "lockdown_display_cleanup_requested",
            "Lockdown display cleanup was requested.",
            {
                "display_count": status.display_count,
                "window_count": status.window_count,
                "active": status.active,
            },
        )
        result = self.lockdown_display_manager.stop()
        self._log_app_route_event(
            "lockdown_display_stopped",
            "Lockdown display windows stopped.",
            {
                "display_count": result.display_count,
                "window_count": result.window_count,
                "fallback_used": result.fallback_used,
                "result_status": result.status,
            },
        )

    def _handle_lockdown_development_escape(self) -> None:
        self._log_app_route_event("lockdown_display_development_escape_used", "Lockdown display development escape was used.")
        self.show_launch_screen()

    def _start_global_shortcut_if_configured(self) -> None:
        if not self.global_shortcut_manager.should_attempt_registration():
            status = self.global_shortcut_manager.build_status()
            if self.global_shortcut_manager.enabled and self.global_shortcut_manager.shortcut_enabled:
                self._log_app_route_event(
                    "global_shortcut_unavailable",
                    status.message,
                    {
                        "available": status.available,
                        "registered": status.registered,
                        "supported_platform": status.supported_platform,
                        "activation_action": status.activation_action,
                    },
                )
            return

        self.global_shortcut_controller = WindowsHotkeyController(
            hotkey=self.global_shortcut_manager.hotkey,
            dispatch_to_gui=self._dispatch_gui_action_from_shortcut,
            on_shortcut_pressed=self._handle_global_shortcut_activation,
        )
        result = self.global_shortcut_controller.start()
        if result.success:
            self._log_app_route_event(
                "global_shortcut_started",
                "Global shortcut support started.",
                {
                    "available": result.available,
                    "registered": result.registered,
                    "activation_action": self.global_shortcut_manager.activation_action,
                },
            )
        else:
            self._log_app_route_event(
                "global_shortcut_registration_failed",
                "Global shortcut support is unavailable.",
                {
                    "available": result.available,
                    "registered": result.registered,
                    "activation_action": self.global_shortcut_manager.activation_action,
                },
            )

    def _stop_global_shortcut(self) -> None:
        if self.global_shortcut_controller is None:
            return
        result = self.global_shortcut_controller.stop()
        self.global_shortcut_controller = None
        if result.success:
            self._log_app_route_event(
                "global_shortcut_stopped",
                "Global shortcut support stopped.",
                {"available": result.available, "registered": result.registered},
            )

    def _dispatch_gui_action_from_shortcut(self, callback: Callable[[], None]) -> None:
        try:
            self.after(0, callback)
        except Exception:
            pass

    def _handle_global_shortcut_activation(self) -> None:
        current_mode = self.mode_manager.current_mode
        metadata = {
            "activation_action": self.global_shortcut_manager.activation_action,
            "route": SafeDeskMode.PUBLIC_LOCK.value,
            "current_mode": current_mode.value,
            "was_hidden_to_tray": self._hidden_to_tray,
        }
        self._log_app_route_event(
            "global_shortcut_activation_requested",
            "Global shortcut requested SafeDesk public lock screen.",
            metadata,
        )

        if self.global_shortcut_manager.activation_action != "public_lock":
            self._log_app_route_event(
                "global_shortcut_activation_skipped",
                "Global shortcut activation was skipped.",
                metadata,
            )
            return

        if current_mode == SafeDeskMode.PUBLIC_LOCK and not self.global_shortcut_manager.allow_when_public_lock_open:
            self._log_app_route_event(
                "global_shortcut_activation_skipped",
                "Global shortcut activation was skipped because public lock is already open.",
                metadata,
            )
            return

        if self._hidden_to_tray and not self.global_shortcut_manager.allow_when_minimized_to_tray:
            self._log_app_route_event(
                "global_shortcut_activation_skipped",
                "Global shortcut activation was skipped while SafeDesk was minimized to tray.",
                metadata,
            )
            return

        if current_mode == SafeDeskMode.ADMIN_CONSOLE and not self.global_shortcut_manager.allow_when_admin_console_open:
            self._log_app_route_event(
                "global_shortcut_activation_skipped",
                "Global shortcut activation was skipped while Admin Console was open.",
                metadata,
            )
            return

        if self._hidden_to_tray:
            self.restore_from_tray()
        else:
            self.deiconify()
            self.lift()
        self.show_public_lock_screen()
        self._log_app_route_event(
            "global_shortcut_public_lock_opened",
            "Global shortcut opened SafeDesk public lock screen.",
            metadata,
        )

    def _tray_controls_available(self) -> bool:
        return (
            self.background_agent_manager.minimize_to_tray
            and self.tray_controller is not None
            and self.tray_controller.tray_running
        )

    def _dispatch_gui_action_from_tray(self, callback: Callable[[], None]) -> None:
        try:
            self.after(0, callback)
        except Exception:
            pass

    def show_launch_screen_from_tray(self) -> None:
        self._log_app_route_event("tray_open_safedesk_requested", "Tray requested SafeDesk launch screen.")
        self.restore_from_tray()
        self.show_launch_screen()

    def show_admin_gate_from_tray(self) -> None:
        self._log_app_route_event("tray_open_admin_gate_requested", "Tray requested Owner/Admin Gate.")
        self.restore_from_tray()
        self.show_admin_gate()

    def show_public_lock_from_tray(self) -> None:
        self._log_app_route_event("tray_public_lock_requested", "Tray requested SafeDesk public lock screen.")
        self.restore_from_tray()
        self.show_public_lock_screen()

    def hide_to_tray(self) -> bool:
        if not self._tray_controls_available():
            self._log_app_route_event(
                "tray_hide_unavailable",
                "SafeDesk could not be minimized to tray because tray support is unavailable.",
                {"tray_available": False, "tray_running": False},
            )
            return False

        self._release_current_screen_resources()
        self.mode_manager.transition_to(SafeDeskMode.BACKGROUND_AGENT)
        self._log_app_route_event(
            "tray_hide_requested",
            "SafeDesk was minimized to the system tray.",
            {"tray_available": True, "tray_running": True},
        )
        self._hidden_to_tray = True
        self.withdraw()
        return True

    def restore_from_tray(self) -> None:
        self._log_app_route_event(
            "tray_restore_requested",
            "SafeDesk was restored from the system tray.",
            {"tray_available": self.tray_controller is not None, "tray_running": self._tray_controls_available()},
        )
        self._hidden_to_tray = False
        self.deiconify()
        self.lift()
        self._resume_current_screen_resources()

    def exit_from_tray(self) -> None:
        self._log_app_route_event("tray_exit_requested", "Tray requested SafeDesk exit.")
        self._stop_lockdown_display()
        if self.tray_controller is not None:
            self.tray_controller.stop()
        self._stop_global_shortcut()
        self.destroy()

    def _handle_window_close(self) -> None:
        if self.background_agent_manager.close_to_tray and self.hide_to_tray():
            return
        self.destroy()

    def _set_admin_active_button(self, screen_name: str | None) -> None:
        for name, button in self.buttons.items():
            button.set_active(name == screen_name)

    def show_launch_screen(self) -> None:
        self._stop_lockdown_display()
        self.mode_manager.transition_to(SafeDeskMode.LAUNCH)
        self._clear_current_screen()
        self._show_route_layout()
        self._set_admin_active_button(None)
        self.current_screen = LaunchScreen(
            self.content,
            self.context,
            on_open_admin_console=self.show_admin_gate,
            on_open_public_lock=self.show_public_lock_screen,
            on_minimize_to_tray=self.hide_to_tray,
            tray_controls_enabled=self._tray_controls_available(),
            on_exit=self.destroy,
        )
        self.current_screen.grid(row=0, column=0, sticky="nsew")
        self._log_app_route_event("launch_screen_opened", "SafeDesk launch screen opened.")

    def _admin_gate_enabled(self) -> bool:
        return self.admin_gate_config.get("enabled", True) is True and self.admin_gate_config.get("foundation_enabled", True) is True

    def show_admin_gate(self, initial_screen: str = HOME) -> None:
        self._stop_lockdown_display()
        if not self._admin_gate_enabled():
            self._log_app_route_event(
                "admin_gate_bypassed_by_config",
                "Owner/Admin Gate is disabled by local configuration.",
                {"initial_screen": initial_screen},
            )
            self._open_admin_console_after_gate(initial_screen)
            return

        self.mode_manager.transition_to(SafeDeskMode.ADMIN_GATE)
        self._clear_current_screen()
        self._show_route_layout()
        self._set_admin_active_button(None)
        self.current_screen = AdminGateScreen(
            self.content,
            self.context,
            self.admin_gate_manager,
            on_gate_success=lambda screen=initial_screen: self._open_admin_console_after_gate(screen),
            on_continue_setup=lambda: self._open_admin_console_after_gate(AUTHENTICATION_SETUP),
            on_back_to_launch=self.show_launch_screen,
        )
        self.current_screen.grid(row=0, column=0, sticky="nsew")
        self._log_app_route_event("admin_gate_opened", "Owner/Admin Gate opened.", {"initial_screen": initial_screen})

    def show_admin_console(self, initial_screen: str = HOME, gate_verified: bool = False) -> None:
        if self._admin_gate_enabled() and not gate_verified:
            self.show_admin_gate(initial_screen)
            return

        self._open_admin_console_after_gate(initial_screen)

    def _open_admin_console_after_gate(self, initial_screen: str = HOME) -> None:
        if self.mode_manager.current_mode != SafeDeskMode.ADMIN_GATE:
            self.mode_manager.transition_to(SafeDeskMode.ADMIN_GATE)
        self.mode_manager.transition_to(SafeDeskMode.ADMIN_CONSOLE)
        self._show_admin_layout()
        self._log_app_route_event(
            "admin_console_opened_after_gate",
            "SafeDesk admin console opened after gate route.",
            {"initial_screen": initial_screen},
        )
        self._show_admin_screen(initial_screen)

    def show_public_lock_screen(self) -> None:
        if not self.public_lock_placeholder_allowed:
            self._log_app_route_event("public_lock_placeholder_blocked", "SafeDesk public lock placeholder is disabled by configuration.")
            return
        if self.mode_manager.current_mode == SafeDeskMode.PUBLIC_LOCK and self.lockdown_display_manager.active:
            self._start_lockdown_display()
            return
        self.mode_manager.transition_to(SafeDeskMode.PUBLIC_LOCK)
        self._clear_current_screen()
        self._show_route_layout()
        self._set_admin_active_button(None)
        self.current_screen = PublicLockScreen(
            self.content,
            self.context,
        )
        self.current_screen.grid(row=0, column=0, sticky="nsew")
        self._log_app_route_event("lock_safedesk_placeholder_requested", "SafeDesk lock placeholder was requested manually.")
        self._log_app_route_event("public_lock_placeholder_opened", "SafeDesk public lock placeholder opened.")
        self._start_lockdown_display()

    def show_screen(self, screen_name: str) -> None:
        if self.mode_manager.current_mode != SafeDeskMode.ADMIN_CONSOLE:
            self.show_admin_gate(screen_name)
            return

        self._show_admin_screen(screen_name)

    def _show_admin_screen(self, screen_name: str) -> None:
        screen_name = self._guard_admin_screen_route(screen_name)
        self._clear_current_screen()

        factory = self.screen_factories.get(screen_name, HomeScreen)
        self.current_screen = factory(self.content, self.context)
        self.current_screen.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        self._set_admin_active_button(screen_name)

    def _guard_admin_screen_route(self, screen_name: str) -> str:
        if screen_name not in SCREEN_NAMES:
            return HOME

        policy_status = self.developer_tools_policy.build_status()
        if admin_route_allowed(
            self.config,
            screen_name,
            effective_environment=self.effective_environment,
        ):
            return screen_name

        self._log_app_route_event(
            "developer_tool_route_blocked",
            "A Developer Tools route was blocked by safe policy.",
            {
                "route": screen_name,
                "result_status": "blocked",
                "demo_routes_allowed": policy_status.demo_routes_allowed,
                "diagnostics_visible": policy_status.diagnostics_visible,
            },
        )
        return HOME

    def _release_current_screen_resources(self) -> None:
        if self.current_screen is not None:
            release = getattr(self.current_screen, "release_resources", None)
            if callable(release):
                release()

    def _resume_current_screen_resources(self) -> None:
        if self.current_screen is not None:
            resume = getattr(self.current_screen, "resume_resources", None)
            if callable(resume):
                resume()

    def destroy(self) -> None:
        if self._destroying:
            return
        self._destroying = True
        if self.startup_maximize_controller is not None:
            self.startup_maximize_controller.cancel()
        self._stop_lockdown_display()
        self._release_current_screen_resources()
        self._stop_global_shortcut()
        if self.tray_controller is not None:
            self.tray_controller.stop()
        super().destroy()

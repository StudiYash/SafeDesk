"""Main SafeDesk GUI shell window."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.app_modes import (
    AppModeManager,
    SafeDeskMode,
    can_open_public_lock_placeholder,
    parse_app_mode,
)
from safedesk.gui import design_system as ds
from safedesk.gui.components.sidebar_button import SidebarButton
from safedesk.gui.navigation import (
    ABOUT,
    AUTHENTICATION_SETUP,
    DASHBOARD,
    EVENT_LOGS,
    FACE_RECOGNITION_DEMO,
    HOME,
    INTRUDER_DETECTION_DEMO,
    LIVENESS_DEMO,
    OWNER_FACE_REGISTRATION,
    OTP_EMAIL_SETUP,
    PROTECTED_MODE_PREVIEW,
    SCREEN_DEFINITIONS,
    SETUP_STATUS,
    SETUP_WIZARD,
    SETTINGS,
    SHUTDOWN_ESCALATION,
    THREAT_LEVEL_DEMO,
)
from safedesk.gui.screens.about_screen import AboutScreen
from safedesk.gui.screens.authentication_setup_screen import AuthenticationSetupScreen
from safedesk.gui.screens.dashboard_placeholder_screen import DashboardPlaceholderScreen
from safedesk.gui.screens.face_recognition_demo_screen import FaceRecognitionDemoScreen
from safedesk.gui.screens.home_screen import HomeScreen
from safedesk.gui.screens.intruder_detection_demo_screen import IntruderDetectionDemoScreen
from safedesk.gui.screens.launch_screen import LaunchScreen
from safedesk.gui.screens.liveness_demo_screen import LivenessDemoScreen
from safedesk.gui.screens.logging_dashboard_screen import LoggingDashboardScreen
from safedesk.gui.screens.owner_face_registration_screen import OwnerFaceRegistrationScreen
from safedesk.gui.screens.otp_email_setup_screen import OtpEmailSetupScreen
from safedesk.gui.screens.protected_mode_preview_screen import ProtectedModePreviewScreen
from safedesk.gui.screens.public_lock_screen import PublicLockScreen
from safedesk.gui.screens.settings_placeholder_screen import SettingsPlaceholderScreen
from safedesk.gui.screens.setup_status_screen import SetupStatusScreen
from safedesk.gui.screens.setup_wizard_screen import SetupWizardScreen
from safedesk.gui.screens.shutdown_escalation_screen import ShutdownEscalationScreen
from safedesk.gui.screens.threat_level_demo_screen import ThreatLevelDemoScreen
from safedesk.gui.theme import apply_theme
from safedesk.logging.event_logger import build_logger_from_config


class SafeDeskMainWindow(ctk.CTk):
    """Safe placeholder desktop shell for SafeDesk."""

    def __init__(self, context: RuntimeContext):
        self.context = context
        self.config = context.load_result.config
        self.ui_config = self.config.get("ui", {})
        self.app_mode_config = self.config.get("app_modes", {})
        self.public_lock_placeholder_allowed = can_open_public_lock_placeholder(self.config)
        self.mode_manager = AppModeManager(self._configured_start_mode())
        self.event_logger = build_logger_from_config(self.config)
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
        self.protocol("WM_DELETE_WINDOW", self.destroy)

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
            THREAT_LEVEL_DEMO: ThreatLevelDemoScreen,
            PROTECTED_MODE_PREVIEW: ProtectedModePreviewScreen,
            SHUTDOWN_ESCALATION: ShutdownEscalationScreen,
            DASHBOARD: DashboardPlaceholderScreen,
            SETTINGS: SettingsPlaceholderScreen,
            ABOUT: AboutScreen,
        }

        self._build_sidebar()
        self._show_initial_mode()

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

        for index, screen in enumerate(SCREEN_DEFINITIONS):
            button = SidebarButton(self.nav_frame, text=screen.label, command=lambda name=screen.name: self.show_screen(name))
            button.grid(row=index, column=0, padx=14, pady=4, sticky="ew")
            self.buttons[screen.name] = button

        self.lock_button = SidebarButton(self.sidebar, text="Lock SafeDesk", command=self.show_public_lock_screen)
        if not self.public_lock_placeholder_allowed:
            self.lock_button.configure(state="disabled")
        self.lock_button.grid(row=4, column=0, padx=14, pady=(0, 16), sticky="ew")

    def _configured_start_mode(self) -> SafeDeskMode:
        configured = parse_app_mode(self.app_mode_config.get("default_start_mode", SafeDeskMode.LAUNCH.value))
        if configured == SafeDeskMode.PUBLIC_LOCK and not self.public_lock_placeholder_allowed:
            return SafeDeskMode.LAUNCH
        if configured in {SafeDeskMode.ADMIN_CONSOLE, SafeDeskMode.PUBLIC_LOCK}:
            return configured
        return SafeDeskMode.LAUNCH

    def _show_initial_mode(self) -> None:
        initial_mode = self.mode_manager.current_mode
        if initial_mode == SafeDeskMode.ADMIN_CONSOLE:
            self.show_admin_console()
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

    def _log_app_route_event(self, action: str, message: str) -> None:
        try:
            self.event_logger.log_app_event(action=action, status="info", message=message, metadata={"mode": self.mode_manager.current_mode.value})
        except Exception:
            pass

    def _set_admin_active_button(self, screen_name: str | None) -> None:
        for name, button in self.buttons.items():
            button.set_active(name == screen_name)

    def show_launch_screen(self) -> None:
        self.mode_manager.transition_to(SafeDeskMode.LAUNCH)
        self._clear_current_screen()
        self._show_route_layout()
        self._set_admin_active_button(None)
        self.current_screen = LaunchScreen(
            self.content,
            self.context,
            on_open_admin_console=self.show_admin_console,
            on_open_public_lock=self.show_public_lock_screen,
            on_exit=self.destroy,
        )
        self.current_screen.grid(row=0, column=0, sticky="nsew")
        self._log_app_route_event("launch_screen_opened", "SafeDesk launch screen opened.")

    def show_admin_console(self, initial_screen: str = HOME) -> None:
        self.mode_manager.transition_to(SafeDeskMode.ADMIN_CONSOLE)
        self._show_admin_layout()
        self._log_app_route_event("admin_console_opened", "SafeDesk admin console opened.")
        self._show_admin_screen(initial_screen)

    def show_public_lock_screen(self) -> None:
        if not self.public_lock_placeholder_allowed:
            self._log_app_route_event("public_lock_placeholder_blocked", "SafeDesk public lock placeholder is disabled by configuration.")
            return
        self.mode_manager.transition_to(SafeDeskMode.PUBLIC_LOCK)
        self._clear_current_screen()
        self._show_route_layout()
        self._set_admin_active_button(None)
        self.current_screen = PublicLockScreen(
            self.content,
            self.context,
            on_return_to_launch=self.show_launch_screen,
            on_return_to_admin_console=self.show_admin_console,
        )
        self.current_screen.grid(row=0, column=0, sticky="nsew")
        self._log_app_route_event("lock_safedesk_placeholder_requested", "SafeDesk lock placeholder was requested manually.")
        self._log_app_route_event("public_lock_placeholder_opened", "SafeDesk public lock placeholder opened.")

    def show_screen(self, screen_name: str) -> None:
        if self.mode_manager.current_mode != SafeDeskMode.ADMIN_CONSOLE:
            self.show_admin_console(screen_name)
            return

        self._show_admin_screen(screen_name)

    def _show_admin_screen(self, screen_name: str) -> None:
        self._clear_current_screen()

        factory = self.screen_factories.get(screen_name, HomeScreen)
        self.current_screen = factory(self.content, self.context)
        self.current_screen.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        self._set_admin_active_button(screen_name)

    def _release_current_screen_resources(self) -> None:
        if self.current_screen is not None:
            release = getattr(self.current_screen, "release_resources", None)
            if callable(release):
                release()

    def destroy(self) -> None:
        self._release_current_screen_resources()
        super().destroy()

"""Main SafeDesk GUI shell window."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.gui.components.sidebar_button import SidebarButton
from safedesk.gui.navigation import (
    ABOUT,
    DASHBOARD,
    FACE_RECOGNITION_DEMO,
    HOME,
    LIVENESS_DEMO,
    OWNER_FACE_REGISTRATION,
    PROTECTED_MODE_PREVIEW,
    SCREEN_DEFINITIONS,
    SETUP_STATUS,
    SETUP_WIZARD,
    SETTINGS,
)
from safedesk.gui.screens.about_screen import AboutScreen
from safedesk.gui.screens.dashboard_placeholder_screen import DashboardPlaceholderScreen
from safedesk.gui.screens.face_recognition_demo_screen import FaceRecognitionDemoScreen
from safedesk.gui.screens.home_screen import HomeScreen
from safedesk.gui.screens.liveness_demo_screen import LivenessDemoScreen
from safedesk.gui.screens.owner_face_registration_screen import OwnerFaceRegistrationScreen
from safedesk.gui.screens.protected_mode_preview_screen import ProtectedModePreviewScreen
from safedesk.gui.screens.settings_placeholder_screen import SettingsPlaceholderScreen
from safedesk.gui.screens.setup_status_screen import SetupStatusScreen
from safedesk.gui.screens.setup_wizard_screen import SetupWizardScreen
from safedesk.gui.theme import apply_theme


class SafeDeskMainWindow(ctk.CTk):
    """Safe placeholder desktop shell for SafeDesk."""

    def __init__(self, context: RuntimeContext):
        self.context = context
        self.ui_config = context.load_result.config.get("ui", {})
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
        self.sidebar.grid_rowconfigure(len(SCREEN_DEFINITIONS) + 3, weight=1)

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=ds.CONTENT_BG)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.current_screen: ctk.CTkFrame | None = None
        self.buttons: dict[str, SidebarButton] = {}
        self.screen_factories: dict[str, Callable[[ctk.CTkFrame, RuntimeContext], ctk.CTkFrame]] = {
            HOME: HomeScreen,
            SETUP_WIZARD: SetupWizardScreen,
            SETUP_STATUS: SetupStatusScreen,
            OWNER_FACE_REGISTRATION: OwnerFaceRegistrationScreen,
            FACE_RECOGNITION_DEMO: FaceRecognitionDemoScreen,
            LIVENESS_DEMO: LivenessDemoScreen,
            PROTECTED_MODE_PREVIEW: ProtectedModePreviewScreen,
            DASHBOARD: DashboardPlaceholderScreen,
            SETTINGS: SettingsPlaceholderScreen,
            ABOUT: AboutScreen,
        }

        self._build_sidebar()
        self.show_screen(HOME)

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

        for index, screen in enumerate(SCREEN_DEFINITIONS, start=3):
            button = SidebarButton(self.sidebar, text=screen.label, command=lambda name=screen.name: self.show_screen(name))
            button.grid(row=index, column=0, padx=14, pady=4, sticky="ew")
            self.buttons[screen.name] = button

    def show_screen(self, screen_name: str) -> None:
        if self.current_screen is not None:
            self._release_current_screen_resources()
            self.current_screen.destroy()

        factory = self.screen_factories.get(screen_name, HomeScreen)
        self.current_screen = factory(self.content, self.context)
        self.current_screen.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        for name, button in self.buttons.items():
            button.set_active(name == screen_name)

    def _release_current_screen_resources(self) -> None:
        if self.current_screen is not None:
            release = getattr(self.current_screen, "release_resources", None)
            if callable(release):
                release()

    def destroy(self) -> None:
        self._release_current_screen_resources()
        super().destroy()

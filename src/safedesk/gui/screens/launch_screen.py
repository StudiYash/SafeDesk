"""SafeDesk launch screen for choosing the app mode."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.app_modes import can_open_admin_console_from_launch, can_open_public_lock_placeholder
from safedesk.gui import design_system as ds
from safedesk.storage.paths import project_root


class LaunchScreen(ctk.CTkFrame):
    """Owner-controlled launch route before admin tools are exposed."""

    def __init__(
        self,
        master,
        context: RuntimeContext,
        on_open_admin_console: Callable[[], None],
        on_open_public_lock: Callable[[], None],
        on_exit: Callable[[], None],
    ):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.config = context.load_result.config
        self.admin_console_allowed = can_open_admin_console_from_launch(self.config)
        self.public_lock_allowed = can_open_public_lock_placeholder(self.config)
        self.logo_image: ctk.CTkImage | None = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        panel = ctk.CTkFrame(self, **ds.card_kwargs())
        panel.grid(row=0, column=0, padx=42, pady=42, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=1)

        content = ctk.CTkFrame(panel, fg_color="transparent")
        content.grid(row=0, column=0, padx=ds.SPACE_XL, pady=ds.SPACE_XL, sticky="ew")
        content.grid_columnconfigure(0, weight=1)

        self._build_logo_widget(content).grid(row=0, column=0, padx=ds.SPACE_XL, pady=(0, ds.SPACE_XL), sticky="n")

        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.grid(row=1, column=0, padx=(64, 64), pady=(ds.SPACE_LG, 0), sticky="ew")
        actions.grid_columnconfigure((0, 1, 2), weight=1, uniform="launch_actions")

        ctk.CTkButton(
            actions,
            text="Open Admin Console",
            command=on_open_admin_console,
            state="normal" if self.admin_console_allowed else "disabled",
            height=42,
            **ds.secondary_button_kwargs(),
        ).grid(row=0, column=0, padx=(0, ds.SPACE_SM), sticky="ew")

        ctk.CTkButton(
            actions,
            text="Lock SafeDesk",
            command=on_open_public_lock,
            state="normal" if self.public_lock_allowed else "disabled",
            height=42,
            **ds.primary_button_kwargs(),
        ).grid(row=0, column=1, padx=ds.SPACE_SM, sticky="ew")

        ctk.CTkButton(
            actions,
            text="Exit",
            command=on_exit,
            height=42,
            **ds.secondary_button_kwargs(),
        ).grid(row=0, column=2, padx=(ds.SPACE_SM, 0), sticky="ew")

    def _build_logo_widget(self, master) -> ctk.CTkLabel:
        logo_path = project_root() / "SafeDesk Logo.png"
        if logo_path.exists():
            try:
                from PIL import Image

                image = Image.open(logo_path)
                width, height = image.size
                max_width = 620
                max_height = 260
                min_width = 420
                target_width = min(max_width, max(min_width, width))
                target_height = max(1, int(target_width * height / width))
                if target_height > max_height:
                    target_height = max_height
                    target_width = max(1, int(target_height * width / height))
                self.logo_image = ctk.CTkImage(light_image=image, dark_image=image, size=(target_width, target_height))
                return ctk.CTkLabel(master, text="", image=self.logo_image)
            except Exception:
                self.logo_image = None

        return ctk.CTkLabel(
            master,
            text="SafeDesk",
            font=ctk.CTkFont(size=34, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
        )

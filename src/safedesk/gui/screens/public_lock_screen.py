"""Safe public lock placeholder for SafeDesk."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds


class PublicLockScreen(ctk.CTkFrame):
    """Minimal non-enforcing public lock placeholder."""

    def __init__(
        self,
        master,
        context: RuntimeContext,
        on_return_to_launch: Callable[[], None],
        on_return_to_admin_console: Callable[[], None],
    ):
        super().__init__(master, fg_color=ds.SAFEDESK_BLACK)
        self.context = context
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=0, padx=44, pady=44, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            content,
            text="SafeDesk Lockdown",
            font=ctk.CTkFont(size=38, weight="bold"),
            text_color=ds.TEXT_PRIMARY,
        ).grid(row=0, column=0, pady=(44, ds.SPACE_SM), sticky="n")

        ctk.CTkLabel(
            content,
            text="This device is protected.",
            font=ctk.CTkFont(size=ds.FONT_H2, weight="bold"),
            text_color=ds.TEXT_SECONDARY,
        ).grid(row=1, column=0, pady=(0, ds.SPACE_SM), sticky="n")

        ctk.CTkLabel(
            content,
            text="Owner verification required.",
            font=ctk.CTkFont(size=ds.FONT_BODY),
            text_color=ds.TEXT_MUTED,
        ).grid(row=2, column=0, pady=(0, ds.SPACE_XL), sticky="n")

        ctk.CTkLabel(
            content,
            text="Development recovery controls are currently enabled.",
            font=ctk.CTkFont(size=ds.FONT_SMALL),
            text_color=ds.TEXT_MUTED,
        ).grid(row=3, column=0, padx=ds.SPACE_XL, pady=(0, ds.SPACE_XL), sticky="ew")

        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.grid(row=5, column=0, pady=(ds.SPACE_XL, 44), sticky="ew")
        actions.grid_columnconfigure((0, 1), weight=1, uniform="lock_actions")

        ctk.CTkButton(
            actions,
            text="Return to Launch",
            command=on_return_to_launch,
            height=40,
            **ds.secondary_button_kwargs(),
        ).grid(row=0, column=0, padx=(0, ds.SPACE_SM), sticky="ew")

        ctk.CTkButton(
            actions,
            text="Return to Admin Console",
            command=on_return_to_admin_console,
            height=40,
            **ds.primary_button_kwargs(),
        ).grid(row=0, column=1, padx=(ds.SPACE_SM, 0), sticky="ew")

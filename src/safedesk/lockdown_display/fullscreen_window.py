"""Fullscreen visual lockdown window wrapper."""

from __future__ import annotations

from collections.abc import Callable
import time
from typing import Any

import customtkinter as ctk

from safedesk.gui import design_system as ds
from safedesk.gui.screens.public_lock_screen import PublicLockScreen
from safedesk.lockdown_display.display_models import DisplayBounds
from safedesk.lockdown_display.window_geometry import build_geometry as _build_geometry


class LockdownFullscreenWindow:
    """Top-level visual lockdown window for one display."""

    def __init__(
        self,
        root,
        context,
        display: DisplayBounds,
        display_config: dict,
        on_development_escape: Callable[[], None] | None = None,
    ):
        self.root = root
        self.context = context
        self.display = display
        self.display_config = display_config
        self.on_development_escape = on_development_escape
        self.window: ctk.CTkToplevel | None = None
        self.lock_screen: PublicLockScreen | None = None
        self.created_at = 0.0

    @property
    def allow_development_escape(self) -> bool:
        return self.display_config.get("allow_development_escape", True) is True

    @property
    def development_escape_timeout_seconds(self) -> int:
        return int(self.display_config.get("development_escape_timeout_seconds", 30))

    def show(self) -> None:
        """Create and show the lockdown display window."""

        if self.window is not None:
            return

        self.created_at = time.monotonic()
        geometry = _build_geometry(self.display.width, self.display.height, self.display.x, self.display.y)
        self.window = ctk.CTkToplevel(self.root)
        self.window.withdraw()
        self.window.title("SafeDesk Lockdown")
        self.window.configure(fg_color=ds.SAFEDESK_BLACK)
        self.window.geometry(geometry)
        self.window.minsize(self.display.width, self.display.height)
        self.window.maxsize(self.display.width, self.display.height)
        self.window.resizable(False, False)
        self.window.grid_columnconfigure(0, weight=1, minsize=self.display.width)
        self.window.grid_rowconfigure(0, weight=1, minsize=self.display.height)
        self.window.update_idletasks()
        self._apply_window_attributes()
        self.window.geometry(geometry)
        self.window.update_idletasks()
        self.window.protocol("WM_DELETE_WINDOW", self._handle_development_escape)

        self.lock_screen = PublicLockScreen(
            self.window,
            self.context,
            forced_width=self.display.width,
            forced_height=self.display.height,
        )
        self.lock_screen.grid(row=0, column=0, sticky="nsew")
        self.lock_screen.configure(width=self.display.width, height=self.display.height)
        self.window.bind("<Control-Shift-Q>", self._handle_development_escape)
        self.window.bind("<Escape>", self._handle_development_escape)
        self.window.deiconify()
        self.window.focus_force()

    def destroy(self) -> None:
        """Destroy this lockdown display window safely."""

        window = self.window
        self.window = None
        self.lock_screen = None
        if window is None:
            return
        try:
            window.destroy()
        except Exception:
            pass

    def _apply_window_attributes(self) -> None:
        if self.window is None:
            return
        if self.display_config.get("borderless_enabled", True) is True:
            try:
                self.window.overrideredirect(True)
            except Exception:
                pass
        if self.display_config.get("topmost_enabled", True) is True:
            try:
                self.window.attributes("-topmost", True)
            except Exception:
                pass

    def _handle_development_escape(self, _event: Any | None = None) -> str:
        if not self.allow_development_escape:
            return "break"
        if time.monotonic() - self.created_at < self.development_escape_timeout_seconds:
            return "break"
        if self.on_development_escape is not None:
            try:
                self.on_development_escape()
            except Exception:
                pass
        return "break"

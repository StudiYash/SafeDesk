"""Passive black per-display lockdown coverage window."""

from __future__ import annotations

from collections.abc import Callable
import time
from typing import Any

import customtkinter as ctk

from safedesk.gui import design_system as ds
from safedesk.lockdown_display.display_models import DisplayBounds
from safedesk.lockdown_display.window_geometry import build_geometry


class BlackoutDisplayWindow:
    """Plain black visual coverage window for a secondary display."""

    def __init__(
        self,
        root,
        _context,
        display: DisplayBounds,
        display_config: dict,
        on_development_escape: Callable[[], None] | None = None,
    ):
        self.root = root
        self.display = display
        self.display_config = display_config
        self.on_development_escape = on_development_escape
        self.window: ctk.CTkToplevel | None = None
        self.created_at = 0.0

    @property
    def allow_development_escape(self) -> bool:
        return self.display_config.get("allow_development_escape", True) is True

    @property
    def development_escape_timeout_seconds(self) -> int:
        return int(self.display_config.get("development_escape_timeout_seconds", 30))

    def show(self) -> None:
        if self.window is not None:
            return

        self.created_at = time.monotonic()
        geometry = build_geometry(self.display.width, self.display.height, self.display.x, self.display.y)
        self.window = ctk.CTkToplevel(self.root)
        self.window.withdraw()
        self.window.title("SafeDesk Lockdown")
        self.window.configure(fg_color=ds.SAFEDESK_BLACK)
        self.window.geometry(geometry)
        self.window.minsize(self.display.width, self.display.height)
        self.window.maxsize(self.display.width, self.display.height)
        self.window.resizable(False, False)
        self._apply_window_attributes()
        self.window.geometry(geometry)
        self.window.protocol("WM_DELETE_WINDOW", self._handle_development_escape)
        self.window.bind("<Control-Shift-Q>", self._handle_development_escape)
        self.window.bind("<Escape>", self._handle_development_escape)
        self.window.deiconify()

    def destroy(self) -> None:
        window = self.window
        self.window = None
        if window is None:
            return
        try:
            window.destroy()
        except Exception:
            pass

    def is_active(self) -> bool:
        if self.window is None:
            return False
        try:
            return bool(self.window.winfo_exists())
        except Exception:
            return False

    def recover_visual_priority(
        self,
        *,
        focus_primary: bool = False,
        lift_window: bool = True,
        reapply_topmost: bool = True,
    ) -> bool:
        del focus_primary
        if not self.is_active() or self.window is None:
            return False
        if lift_window:
            try:
                self.window.lift()
            except Exception:
                pass
        if reapply_topmost and self.display_config.get("topmost_enabled", True) is True:
            try:
                self.window.attributes("-topmost", True)
            except Exception:
                pass
        return True

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

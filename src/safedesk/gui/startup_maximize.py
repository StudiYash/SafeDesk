"""One-time mapped-window startup maximization."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

STARTUP_MAXIMIZE_DELAY_MS = 100
STARTUP_MAXIMIZE_MAX_ATTEMPTS = 3


class StartupMaximizeController:
    """Request the normal maximized state only after the root is mapped."""

    def __init__(
        self,
        window: Any,
        *,
        requested: bool,
        destroying: Callable[[], bool] | None = None,
        delay_ms: int = STARTUP_MAXIMIZE_DELAY_MS,
        max_attempts: int = STARTUP_MAXIMIZE_MAX_ATTEMPTS,
    ):
        self.window = window
        self.requested = requested is True
        self.destroying = destroying or (lambda: False)
        self.delay_ms = max(1, int(delay_ms))
        self.max_attempts = max(1, int(max_attempts))
        self.attempt_count = 0
        self._armed = False
        self._completed = False
        self._cancelled = False
        self._after_id = None
        self._map_binding_id = None

    def arm(self) -> bool:
        if not self.requested or self._armed or self._completed or self._cancelled:
            return False
        self._armed = True
        try:
            self._map_binding_id = self.window.bind("<Map>", self._on_mapped, add="+")
        except Exception:
            self._map_binding_id = None
            return False

        try:
            already_mapped = bool(self.window.winfo_ismapped())
        except Exception:
            already_mapped = False
        if already_mapped:
            self._remove_map_binding()
            self._schedule_attempt()
        return True

    def cancel(self) -> None:
        if self._cancelled:
            return
        self._cancelled = True
        if self._after_id is not None:
            try:
                self.window.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        self._remove_map_binding()

    def _on_mapped(self, event=None) -> None:
        if event is not None and getattr(event, "widget", self.window) is not self.window:
            return
        self._remove_map_binding()
        self._schedule_attempt()

    def _schedule_attempt(self) -> None:
        self._schedule(self._attempt_maximize)

    def _schedule_verification(self) -> None:
        self._schedule(self._verify_maximized)

    def _schedule(self, callback: Callable[[], None]) -> None:
        if self._should_stop() or self._after_id is not None:
            return
        try:
            self._after_id = self.window.after(self.delay_ms, callback)
        except Exception:
            self._after_id = None
            self._completed = True
            self._remove_map_binding()

    def _attempt_maximize(self) -> None:
        self._after_id = None
        if self._should_stop():
            return

        self.attempt_count += 1
        try:
            self.window.update_idletasks()
            self.window.wm_state("zoomed")
        except Exception:
            if self.attempt_count >= self.max_attempts:
                self._completed = True
                self._remove_map_binding()
            else:
                self._schedule_attempt()
            return

        self._schedule_verification()

    def _verify_maximized(self) -> None:
        self._after_id = None
        if self._should_stop():
            return

        try:
            accepted = str(self.window.wm_state()).lower() == "zoomed"
        except Exception:
            accepted = False

        if accepted or self.attempt_count >= self.max_attempts:
            self._completed = True
            self._remove_map_binding()
            return
        self._schedule_attempt()

    def _should_stop(self) -> bool:
        if self._cancelled or self._completed:
            return True
        try:
            return self.destroying() is True
        except Exception:
            return True

    def _remove_map_binding(self) -> None:
        if self._map_binding_id is None:
            return
        try:
            self.window.unbind("<Map>", self._map_binding_id)
        except Exception:
            pass
        self._map_binding_id = None

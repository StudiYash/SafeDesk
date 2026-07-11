"""Safe interaction-lock lifecycle and visual recovery manager."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from safedesk.interaction_lock.interaction_lock_models import (
    InteractionLockOperationResult,
    InteractionLockStatus,
)


class SafeInteractionLockManager:
    """Maintain visual lockdown priority without input blocking or hooks."""

    def __init__(
        self,
        config: dict,
        *,
        window_provider: Callable[[], Iterable[Any]] | None = None,
        event_callback: Callable[[str, str, dict], None] | None = None,
    ):
        self.config = config
        raw_config = config.get("safe_interaction_lock", {}) if isinstance(config, dict) else {}
        self.lock_config = raw_config if isinstance(raw_config, dict) else {}
        self.window_provider = window_provider
        self.event_callback = event_callback
        self.root: Any | None = None
        self._after_id: Any | None = None
        self._active = False
        self.tick_count = 0
        self.last_window_count = 0

    @property
    def enabled(self) -> bool:
        return self.lock_config.get("enabled", True) is True

    @property
    def foundation_enabled(self) -> bool:
        return self.lock_config.get("foundation_enabled", True) is True

    @property
    def demo_only(self) -> bool:
        return self.lock_config.get("demo_only", True) is True

    @property
    def focus_recovery_enabled(self) -> bool:
        return self.lock_config.get("focus_recovery_enabled", True) is True

    @property
    def recovery_interval_seconds(self) -> float:
        return float(self.lock_config.get("focus_recovery_interval_seconds", 2))

    @property
    def focus_primary_on_activation(self) -> bool:
        return self.lock_config.get("focus_primary_on_activation", True) is True

    @property
    def focus_primary_on_recovery(self) -> bool:
        return self.lock_config.get("focus_primary_on_recovery", False) is True

    @property
    def lift_windows_on_recovery(self) -> bool:
        return self.lock_config.get("lift_windows_on_recovery", True) is True

    @property
    def reapply_topmost_on_recovery(self) -> bool:
        return self.lock_config.get("reapply_topmost_on_recovery", True) is True

    @property
    def cleanup_on_route_change(self) -> bool:
        return self.lock_config.get("cleanup_on_route_change", True) is True

    @property
    def prevent_duplicate_activation(self) -> bool:
        return self.lock_config.get("prevent_duplicate_activation", True) is True

    @property
    def log_lifecycle_events(self) -> bool:
        return self.lock_config.get("log_lifecycle_events", True) is True

    @property
    def active(self) -> bool:
        return self._active

    def build_status(self) -> InteractionLockStatus:
        """Build a safe lifecycle status summary."""

        if not self.enabled:
            message = "Safe interaction lock is disabled."
        elif not self.foundation_enabled:
            message = "Safe interaction lock foundation is unavailable."
        elif not self.demo_only:
            message = "Safe interaction lock requires demo-only mode in this phase."
        elif not self.focus_recovery_enabled:
            message = "Safe interaction lock focus recovery is disabled."
        elif self.active:
            message = "Safe interaction lock is active."
        else:
            message = "Safe interaction lock is inactive."

        return InteractionLockStatus(
            enabled=self.enabled,
            foundation_enabled=self.foundation_enabled,
            demo_only=self.demo_only,
            active=self.active,
            focus_recovery_enabled=self.focus_recovery_enabled,
            recovery_interval_seconds=self.recovery_interval_seconds,
            tick_count=self.tick_count,
            last_window_count=self.last_window_count,
            message=message,
        )

    def start(
        self,
        root: Any,
        window_provider: Callable[[], Iterable[Any]] | None = None,
    ) -> InteractionLockOperationResult:
        """Start periodic safe visual recovery."""

        if self.active:
            self._emit_event(
                "safe_interaction_lock_start_skipped",
                "Safe interaction lock is already active.",
                {"active": True, "window_count": self.last_window_count, "result_status": "already_active"},
            )
            return InteractionLockOperationResult(
                True,
                "already_active",
                "Safe interaction lock is already active.",
                True,
                self.last_window_count,
            )

        if not self.enabled:
            return self._start_skipped("disabled", "Safe interaction lock is disabled.")
        if not self.foundation_enabled:
            return self._start_skipped("disabled", "Safe interaction lock foundation is unavailable.")
        if not self.demo_only:
            return self._start_skipped("blocked", "Safe interaction lock requires demo-only mode in this phase.")
        if not self.focus_recovery_enabled:
            return self._start_skipped("disabled", "Safe interaction lock focus recovery is disabled.")

        if window_provider is not None:
            self.window_provider = window_provider
        self.root = root
        self._active = True
        self.tick_count = 0
        self.last_window_count = self._window_count()
        self._schedule_next_tick()
        self._emit_event(
            "safe_interaction_lock_started",
            "Safe interaction lock started.",
            {
                "active": True,
                "window_count": self.last_window_count,
                "interval_seconds": self.recovery_interval_seconds,
                "result_status": "started",
            },
        )
        return InteractionLockOperationResult(
            True,
            "started",
            "Safe interaction lock started.",
            True,
            self.last_window_count,
        )

    def stop(self) -> InteractionLockOperationResult:
        """Stop scheduled recovery safely."""

        was_active = self.active
        previous_window_count = self.last_window_count
        self._active = False
        cancelled = self._cancel_timer()
        self.root = None
        if not was_active:
            return InteractionLockOperationResult(True, "not_active", "Safe interaction lock is not active.", False, 0)

        self._emit_event(
            "safe_interaction_lock_stopped",
            "Safe interaction lock stopped.",
            {
                "active": False,
                "window_count": previous_window_count,
                "tick_count": self.tick_count,
                "timer_cancelled": cancelled,
                "result_status": "stopped",
            },
        )
        return InteractionLockOperationResult(
            True,
            "stopped",
            "Safe interaction lock stopped.",
            False,
            previous_window_count,
        )

    def recover_once(self, *, focus_primary: bool | None = None) -> InteractionLockOperationResult:
        """Run one safe visual recovery pass."""

        should_focus_primary = self.focus_primary_on_recovery if focus_primary is None else focus_primary
        recovered = self._recover_windows(focus_primary=should_focus_primary)
        self._emit_event(
            "safe_interaction_lock_recover_once",
            "Safe interaction lock visual recovery was requested.",
            {
                "active": self.active,
                "window_count": self.last_window_count,
                "recovered_window_count": recovered,
                "focus_primary": should_focus_primary,
                "result_status": "recovered",
            },
        )
        return InteractionLockOperationResult(
            True,
            "recovered",
            "Safe interaction lock visual recovery completed.",
            self.active,
            recovered,
        )

    def _start_skipped(self, status: str, message: str) -> InteractionLockOperationResult:
        self._emit_event(
            "safe_interaction_lock_start_skipped",
            message,
            {"active": False, "window_count": 0, "result_status": status},
        )
        return InteractionLockOperationResult(False, status, message, False, 0)

    def _schedule_next_tick(self) -> None:
        if not self.active or self.root is None or self._after_id is not None:
            return
        try:
            interval_ms = int(max(1.0, self.recovery_interval_seconds) * 1000)
            self._after_id = self.root.after(interval_ms, self._handle_recovery_tick)
        except Exception:
            self._after_id = None

    def _handle_recovery_tick(self) -> None:
        self._after_id = None
        if not self.active:
            return
        self.tick_count += 1
        self._recover_windows(focus_primary=self.focus_primary_on_recovery)
        self._schedule_next_tick()

    def _cancel_timer(self) -> bool:
        after_id = self._after_id
        self._after_id = None
        if after_id is None or self.root is None:
            return False
        try:
            self.root.after_cancel(after_id)
            self._emit_event(
                "safe_interaction_lock_timer_cancelled",
                "Safe interaction lock timer was cancelled.",
                {"active": self.active, "tick_count": self.tick_count, "result_status": "cancelled"},
            )
            return True
        except Exception:
            return False

    def _recover_windows(self, *, focus_primary: bool) -> int:
        windows = self._active_windows()
        self.last_window_count = len(windows)
        recovered = 0
        for index, window in enumerate(windows):
            recover = getattr(window, "recover_visual_priority", None)
            if not callable(recover):
                continue
            try:
                if recover(
                    focus_primary=bool(focus_primary and index == 0),
                    lift_window=self.lift_windows_on_recovery,
                    reapply_topmost=self.reapply_topmost_on_recovery,
                ):
                    recovered += 1
            except Exception:
                continue
        return recovered

    def _window_count(self) -> int:
        return len(self._active_windows())

    def _active_windows(self) -> tuple[Any, ...]:
        if self.window_provider is None:
            return ()
        try:
            return tuple(self.window_provider())
        except Exception:
            return ()

    def _emit_event(self, action: str, message: str, metadata: dict) -> None:
        if not self.log_lifecycle_events or self.event_callback is None:
            return
        try:
            self.event_callback(action, message, dict(metadata))
        except Exception:
            pass

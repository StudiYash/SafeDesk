"""Manager for SafeDesk fullscreen lockdown display windows."""

from __future__ import annotations

from collections.abc import Callable, Iterable
import sys
from typing import Any

from safedesk.lockdown_display.display_models import (
    DisplayBounds,
    LockdownDisplayOperationResult,
    LockdownDisplayStatus,
)


class LockdownDisplayManager:
    """Create and clean up visual lockdown windows without enforcement."""

    def __init__(
        self,
        config: dict,
        *,
        display_provider: Callable[[], Iterable[DisplayBounds]] | None = None,
        primary_window_factory: Callable[[Any, Any, DisplayBounds, dict, Callable[[], None] | None], Any] | None = None,
        blackout_window_factory: Callable[[Any, Any, DisplayBounds, dict, Callable[[], None] | None], Any] | None = None,
    ):
        self.config = config
        raw_config = config.get("lockdown_display", {}) if isinstance(config, dict) else {}
        self.display_config = raw_config if isinstance(raw_config, dict) else {}
        self.display_provider = display_provider
        self.primary_window_factory = primary_window_factory
        self.blackout_window_factory = blackout_window_factory
        self.windows: list[Any] = []
        self.last_display_count = 0
        self.fallback_used = False
        self._on_development_escape: Callable[[], None] | None = None

    @property
    def enabled(self) -> bool:
        return self.display_config.get("enabled", True) is True

    @property
    def foundation_enabled(self) -> bool:
        return self.display_config.get("foundation_enabled", True) is True

    @property
    def demo_only(self) -> bool:
        return self.display_config.get("demo_only", True) is True

    @property
    def fullscreen_enabled(self) -> bool:
        return self.display_config.get("fullscreen_enabled", True) is True

    @property
    def multi_display_enabled(self) -> bool:
        return self.display_config.get("multi_display_enabled", True) is True

    @property
    def fallback_to_primary_display(self) -> bool:
        return self.display_config.get("fallback_to_primary_display", True) is True

    @property
    def max_display_windows(self) -> int:
        return int(self.display_config.get("max_display_windows", 6))

    @property
    def active(self) -> bool:
        return bool(self.windows)

    def build_status(self) -> LockdownDisplayStatus:
        """Build a safe status summary."""

        if not self.enabled:
            message = "Lockdown display foundation is disabled."
        elif not self.foundation_enabled:
            message = "Lockdown display foundation is not available."
        elif not self.demo_only:
            message = "Lockdown display requires demo-only mode in this phase."
        elif self.active:
            message = "Lockdown display windows are active."
        else:
            message = "Lockdown display windows are inactive."

        return LockdownDisplayStatus(
            enabled=self.enabled,
            foundation_enabled=self.foundation_enabled,
            demo_only=self.demo_only,
            fullscreen_enabled=self.fullscreen_enabled,
            multi_display_enabled=self.multi_display_enabled,
            active=self.active,
            display_count=self.last_display_count,
            window_count=len(self.windows),
            message=message,
        )

    def detect_displays(self, root: Any | None = None) -> tuple[DisplayBounds, ...]:
        """Detect display bounds with a safe primary-display fallback."""

        displays, _fallback_used = self._detect_displays(root)
        return displays

    def start(
        self,
        root: Any,
        context: Any,
        *,
        on_development_escape: Callable[[], None] | None = None,
    ) -> LockdownDisplayOperationResult:
        """Start visual lockdown windows if configured and available."""

        if self.active:
            return LockdownDisplayOperationResult(
                True,
                "already_active",
                "Lockdown display is already active.",
                self.last_display_count,
                len(self.windows),
                self.fallback_used,
            )
        if not self.enabled:
            return LockdownDisplayOperationResult(False, "disabled", "Lockdown display foundation is disabled.")
        if not self.foundation_enabled:
            return LockdownDisplayOperationResult(False, "disabled", "Lockdown display foundation is not available.")
        if not self.demo_only:
            return LockdownDisplayOperationResult(False, "blocked", "Lockdown display requires demo-only mode in this phase.")
        if not self.fullscreen_enabled:
            return LockdownDisplayOperationResult(False, "disabled", "Fullscreen lockdown display is disabled.")

        displays, fallback_used = self._detect_displays(root)
        self.last_display_count = len(displays)
        self.fallback_used = fallback_used
        if not displays:
            return LockdownDisplayOperationResult(False, "unavailable", "Lockdown display could not detect a usable display.")

        self._on_development_escape = on_development_escape
        created_windows: list[Any] = []
        primary_created = False
        for display in displays:
            try:
                if display.primary and not primary_created:
                    window = self._create_primary_window(root, context, display)
                    primary_created = True
                else:
                    window = self._create_blackout_window(root, context, display)
                show = getattr(window, "show", None)
                if callable(show):
                    show()
                created_windows.append(window)
            except Exception:
                continue

        self.windows = created_windows
        if not self.windows:
            self._on_development_escape = None
            return LockdownDisplayOperationResult(
                False,
                "unavailable",
                "Lockdown display windows could not be created.",
                len(displays),
                0,
                fallback_used,
            )

        return LockdownDisplayOperationResult(
            True,
            "started",
            "Lockdown display windows started.",
            len(displays),
            len(self.windows),
            fallback_used,
        )

    def stop(self) -> LockdownDisplayOperationResult:
        """Destroy visual lockdown windows safely."""

        if not self.windows:
            self._on_development_escape = None
            return LockdownDisplayOperationResult(True, "not_active", "Lockdown display is not active.")

        previous_display_count = self.last_display_count
        previous_window_count = len(self.windows)
        for window in tuple(self.windows):
            destroy = getattr(window, "destroy", None)
            if callable(destroy):
                try:
                    destroy()
                except Exception:
                    pass
        self.windows = []
        self._on_development_escape = None
        return LockdownDisplayOperationResult(
            True,
            "stopped",
            "Lockdown display windows stopped.",
            previous_display_count,
            previous_window_count,
            self.fallback_used,
        )

    def _handle_development_escape(self) -> None:
        callback = self._on_development_escape
        self.stop()
        if callback is not None:
            try:
                callback()
            except Exception:
                pass

    def _create_primary_window(self, root: Any, context: Any, display: DisplayBounds) -> Any:
        if self.primary_window_factory is not None:
            return self.primary_window_factory(root, context, display, self.display_config, self._handle_development_escape)
        from safedesk.lockdown_display.fullscreen_window import LockdownFullscreenWindow

        return LockdownFullscreenWindow(root, context, display, self.display_config, self._handle_development_escape)

    def _create_blackout_window(self, root: Any, context: Any, display: DisplayBounds) -> Any:
        if self.blackout_window_factory is not None:
            return self.blackout_window_factory(root, context, display, self.display_config, self._handle_development_escape)
        from safedesk.lockdown_display.blackout_window import BlackoutDisplayWindow

        return BlackoutDisplayWindow(root, context, display, self.display_config, self._handle_development_escape)

    def _detect_displays(self, root: Any | None) -> tuple[tuple[DisplayBounds, ...], bool]:
        displays: list[DisplayBounds] = []
        fallback_used = False

        if self.display_provider is not None:
            try:
                displays = list(self.display_provider())
            except Exception:
                displays = []
        elif self.multi_display_enabled:
            windows_displays = self._sanitize_displays(self._detect_with_windows_ctypes())
            screeninfo_displays = self._sanitize_displays(self._detect_with_screeninfo())
            displays = self._select_display_source(windows_displays, screeninfo_displays)

        displays = self._sanitize_displays(displays)
        if not displays and self.fallback_to_primary_display:
            displays = [self._fallback_display(root)]
            fallback_used = True
        elif displays and not any(display.primary for display in displays):
            displays[0] = DisplayBounds(
                index=displays[0].index,
                x=displays[0].x,
                y=displays[0].y,
                width=displays[0].width,
                height=displays[0].height,
                primary=True,
            )

        displays.sort(key=lambda display: (not display.primary, display.index))
        return tuple(displays[: self.max_display_windows]), fallback_used

    def _select_display_source(
        self,
        windows_displays: Iterable[DisplayBounds],
        screeninfo_displays: Iterable[DisplayBounds],
    ) -> list[DisplayBounds]:
        windows = list(windows_displays)
        screeninfo = list(screeninfo_displays)
        if not windows:
            return screeninfo
        if not screeninfo:
            return windows
        if self._should_prefer_screeninfo(windows, screeninfo):
            return screeninfo
        return windows

    def _should_prefer_screeninfo(self, windows: list[DisplayBounds], screeninfo: list[DisplayBounds]) -> bool:
        if len(windows) != len(screeninfo):
            return False
        windows_total_area = self._display_area_total(windows)
        screeninfo_total_area = self._display_area_total(screeninfo)
        if windows_total_area <= 0 or screeninfo_total_area <= 0:
            return False

        windows_primary = self._primary_display(windows)
        screeninfo_primary = self._primary_display(screeninfo)
        if (
            windows_primary is not None
            and screeninfo_primary is not None
            and self._is_significantly_larger(screeninfo_primary, windows_primary)
        ):
            return True

        if screeninfo_total_area > windows_total_area * 1.2:
            for windows_display, screeninfo_display in zip(windows, screeninfo):
                if self._is_significantly_larger(screeninfo_display, windows_display):
                    return True
        return False

    def _display_area_total(self, displays: Iterable[DisplayBounds]) -> int:
        return sum(max(0, display.width) * max(0, display.height) for display in displays)

    def _primary_display(self, displays: Iterable[DisplayBounds]) -> DisplayBounds | None:
        display_list = list(displays)
        for display in display_list:
            if display.primary:
                return display
        return display_list[0] if display_list else None

    def _is_significantly_larger(self, candidate: DisplayBounds, baseline: DisplayBounds) -> bool:
        baseline_area = max(0, baseline.width) * max(0, baseline.height)
        candidate_area = max(0, candidate.width) * max(0, candidate.height)
        if baseline_area <= 0:
            return False
        return candidate_area > baseline_area * 1.2 and (
            candidate.width > baseline.width * 1.15 or candidate.height > baseline.height * 1.15
        )

    def _detect_with_windows_ctypes(self) -> list[DisplayBounds]:
        if sys.platform != "win32":
            return []

        try:
            import ctypes
            from ctypes import wintypes
        except Exception:
            return []

        try:
            class Rect(ctypes.Structure):
                _fields_ = (
                    ("left", wintypes.LONG),
                    ("top", wintypes.LONG),
                    ("right", wintypes.LONG),
                    ("bottom", wintypes.LONG),
                )

            class MonitorInfo(ctypes.Structure):
                _fields_ = (
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", Rect),
                    ("rcWork", Rect),
                    ("dwFlags", wintypes.DWORD),
                )

            hmonitor_type = getattr(wintypes, "HMONITOR", wintypes.HANDLE)
            hdc_type = getattr(wintypes, "HDC", wintypes.HANDLE)
            monitor_enum_proc = ctypes.WINFUNCTYPE(
                wintypes.BOOL,
                hmonitor_type,
                hdc_type,
                ctypes.POINTER(Rect),
                wintypes.LPARAM,
            )
            user32 = ctypes.windll.user32
        except Exception:
            return []

        displays: list[DisplayBounds] = []

        def _append_monitor(hmonitor, _hdc, _rect, _data):
            info = MonitorInfo()
            info.cbSize = ctypes.sizeof(MonitorInfo)
            try:
                if not user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
                    return True
                rect = info.rcMonitor
                width = int(rect.right - rect.left)
                height = int(rect.bottom - rect.top)
                if width <= 0 or height <= 0:
                    return True
                displays.append(
                    DisplayBounds(
                        index=len(displays),
                        x=int(rect.left),
                        y=int(rect.top),
                        width=width,
                        height=height,
                        primary=bool(info.dwFlags & 1),
                    )
                )
            except Exception:
                return True
            return True

        try:
            callback = monitor_enum_proc(_append_monitor)
            user32.EnumDisplayMonitors(None, None, callback, 0)
        except Exception:
            return []

        return displays

    def _detect_with_screeninfo(self) -> list[DisplayBounds]:
        try:
            from screeninfo import get_monitors
        except Exception:
            return []

        displays: list[DisplayBounds] = []
        try:
            monitors = get_monitors()
        except Exception:
            return []

        for index, monitor in enumerate(monitors):
            try:
                displays.append(
                    DisplayBounds(
                        index=index,
                        x=int(getattr(monitor, "x", 0)),
                        y=int(getattr(monitor, "y", 0)),
                        width=int(getattr(monitor, "width", 0)),
                        height=int(getattr(monitor, "height", 0)),
                        primary=bool(getattr(monitor, "is_primary", index == 0)),
                    )
                )
            except Exception:
                continue
        return displays

    def _sanitize_displays(self, displays: Iterable[DisplayBounds]) -> list[DisplayBounds]:
        clean: list[DisplayBounds] = []
        for index, display in enumerate(displays):
            try:
                width = int(display.width)
                height = int(display.height)
                if width <= 0 or height <= 0:
                    continue
                clean.append(
                    DisplayBounds(
                        index=index,
                        x=int(display.x),
                        y=int(display.y),
                        width=width,
                        height=height,
                        primary=bool(display.primary),
                    )
                )
            except Exception:
                continue
        return clean[: self.max_display_windows]

    def _fallback_display(self, root: Any | None) -> DisplayBounds:
        width = 1024
        height = 768
        if root is not None:
            try:
                width = max(1, int(root.winfo_screenwidth()))
                height = max(1, int(root.winfo_screenheight()))
            except Exception:
                pass
        return DisplayBounds(index=0, x=0, y=0, width=width, height=height, primary=True)

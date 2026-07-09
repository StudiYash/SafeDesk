"""Windows registered-hotkey controller for SafeDesk Phase 20."""

from __future__ import annotations

from collections.abc import Callable
import platform
import threading
from typing import Any

from safedesk.global_shortcut.shortcut_manager import parse_hotkey
from safedesk.global_shortcut.shortcut_models import ShortcutOperationResult

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
PM_NOREMOVE = 0x0000
SAFEDESK_HOTKEY_ID = 0x5344


class WindowsHotkeyController:
    """Register one configured Windows hotkey without monitoring typed input."""

    def __init__(
        self,
        *,
        hotkey: str,
        dispatch_to_gui: Callable[[Callable[[], None]], None],
        on_shortcut_pressed: Callable[[], None],
        platform_name: str | None = None,
        hotkey_id: int = SAFEDESK_HOTKEY_ID,
    ):
        self.hotkey = hotkey
        self.dispatch_to_gui = dispatch_to_gui
        self.on_shortcut_pressed = on_shortcut_pressed
        self.platform_name = platform_name or platform.system()
        self.hotkey_id = hotkey_id
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._registered = False
        self._running = False
        self._registration_event = threading.Event()
        self._registration_result: ShortcutOperationResult | None = None

    @property
    def registered(self) -> bool:
        return self._registered

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> ShortcutOperationResult:
        """Register the configured hotkey on Windows when available."""

        if self._running or self._registered:
            return ShortcutOperationResult(True, "already_running", "Global shortcut is already registered.", True, True)

        if self.platform_name != "Windows":
            return ShortcutOperationResult(False, "unavailable", "Global shortcut support is unavailable on this platform.", False, False)

        hotkey_result = parse_hotkey(self.hotkey)
        if not hotkey_result.success:
            return ShortcutOperationResult(False, hotkey_result.status, hotkey_result.message, False, False)

        self._registration_event.clear()
        self._registration_result = None
        self._thread = threading.Thread(
            target=self._message_loop,
            args=(hotkey_result.modifiers, hotkey_result.virtual_key),
            name="SafeDeskGlobalShortcut",
            daemon=True,
        )
        self._thread.start()
        if not self._registration_event.wait(timeout=1.5):
            return ShortcutOperationResult(False, "registration_timeout", "Global shortcut registration did not complete.", False, False)
        return self._registration_result or ShortcutOperationResult(
            False,
            "registration_failed",
            "Global shortcut could not be registered.",
            False,
            False,
        )

    def stop(self) -> ShortcutOperationResult:
        """Stop shortcut registration safely."""

        if not self._running and not self._registered:
            return ShortcutOperationResult(True, "not_running", "Global shortcut is not running.", False, False)

        self._post_quit_message()
        thread = self._thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1)

        still_running = bool(thread is not None and thread.is_alive())
        if still_running:
            return ShortcutOperationResult(False, "stop_pending", "Global shortcut stop is pending.", self._registered, self._running)
        self._thread = None
        self._thread_id = None
        self._running = False
        self._registered = False
        return ShortcutOperationResult(True, "stopped", "Global shortcut stopped.", False, False)

    def _message_loop(self, modifiers: int, virtual_key: int) -> None:
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            msg = wintypes.MSG()
            self._thread_id = int(kernel32.GetCurrentThreadId())
            user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_NOREMOVE)

            if not user32.RegisterHotKey(None, self.hotkey_id, modifiers, virtual_key):
                self._registered = False
                self._running = False
                self._registration_result = ShortcutOperationResult(
                    False,
                    "registration_failed",
                    "Global shortcut could not be registered.",
                    False,
                    False,
                )
                self._registration_event.set()
                return

            self._registered = True
            self._running = True
            self._registration_result = ShortcutOperationResult(True, "started", "Global shortcut registered.", True, True)
            self._registration_event.set()

            while self._running:
                message_result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if message_result in (0, -1):
                    break
                if msg.message == WM_HOTKEY and int(msg.wParam) == self.hotkey_id:
                    self._dispatch_activation()
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception:
            self._registered = False
            self._running = False
            self._registration_result = ShortcutOperationResult(
                False,
                "unavailable",
                "Global shortcut support is unavailable.",
                False,
                False,
            )
            self._registration_event.set()
        finally:
            self._unregister_hotkey()
            self._registered = False
            self._running = False

    def _dispatch_activation(self) -> None:
        try:
            self.dispatch_to_gui(self.on_shortcut_pressed)
        except Exception:
            pass

    def _post_quit_message(self) -> None:
        if self.platform_name != "Windows" or self._thread_id is None:
            self._running = False
            return
        try:
            import ctypes

            ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        except Exception:
            self._running = False

    def _unregister_hotkey(self) -> None:
        if not self._registered or self.platform_name != "Windows":
            return
        try:
            import ctypes

            ctypes.windll.user32.UnregisterHotKey(None, self.hotkey_id)
        except Exception:
            pass

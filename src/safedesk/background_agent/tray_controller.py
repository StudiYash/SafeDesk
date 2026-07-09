"""Optional system-tray controller for SafeDesk Phase 19."""

from __future__ import annotations

from collections.abc import Callable
import threading
from typing import Any

from safedesk.background_agent.background_agent_models import TrayOperationResult
from safedesk.storage.paths import project_root


class TrayController:
    """Small optional pystray wrapper that dispatches GUI work safely."""

    def __init__(
        self,
        *,
        dispatch_to_gui: Callable[[Callable[[], None]], None],
        on_open_safedesk: Callable[[], None],
        on_open_admin_console: Callable[[], None],
        on_lock_safedesk: Callable[[], None],
        on_exit_safedesk: Callable[[], None],
        allow_exit: bool = True,
    ):
        self.dispatch_to_gui = dispatch_to_gui
        self.on_open_safedesk = on_open_safedesk
        self.on_open_admin_console = on_open_admin_console
        self.on_lock_safedesk = on_lock_safedesk
        self.on_exit_safedesk = on_exit_safedesk
        self.allow_exit = allow_exit
        self.icon: Any | None = None
        self._pystray: Any | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._available = False

    @property
    def tray_available(self) -> bool:
        return self._available

    @property
    def tray_running(self) -> bool:
        return self._running

    def start(self) -> TrayOperationResult:
        """Start the optional tray icon when dependencies are available."""

        if self._running:
            return TrayOperationResult(True, "already_running", "System tray support is already running.", True, True)

        pystray = self._load_pystray_module()
        if pystray is None:
            self._available = False
            self._running = False
            return TrayOperationResult(False, "unavailable", "System tray support is unavailable.", False, False)

        icon_image = self._build_icon_image()
        if icon_image is None:
            self._available = False
            self._running = False
            return TrayOperationResult(False, "unavailable", "System tray support is unavailable.", False, False)

        menu_items = [
            pystray.MenuItem("Open SafeDesk", self._menu_open_safedesk),
            pystray.MenuItem("Open Admin Console", self._menu_open_admin_console),
            pystray.MenuItem("Lock SafeDesk", self._menu_lock_safedesk),
            pystray.Menu.SEPARATOR,
        ]
        if self.allow_exit:
            menu_items.append(pystray.MenuItem("Exit SafeDesk", self._menu_exit_safedesk))

        self._pystray = pystray
        self.icon = pystray.Icon("SafeDesk", icon_image, "SafeDesk", pystray.Menu(*menu_items))
        self._available = True
        self._running = True
        self._thread = threading.Thread(target=self._run_icon, name="SafeDeskTray", daemon=True)
        self._thread.start()
        return TrayOperationResult(True, "started", "System tray support started.", True, True)

    def stop(self) -> TrayOperationResult:
        """Stop the optional tray icon without affecting local data."""

        icon = self.icon
        if icon is None and not self._running:
            return TrayOperationResult(True, "not_running", "System tray support is not running.", self._available, False)

        try:
            if icon is not None:
                icon.stop()
        except Exception:
            return TrayOperationResult(False, "stop_failed", "System tray support could not be stopped cleanly.", self._available, self._running)

        self._running = False
        self.icon = None
        thread = self._thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1)
        self._thread = None
        return TrayOperationResult(True, "stopped", "System tray support stopped.", self._available, False)

    def _load_pystray_module(self) -> Any | None:
        try:
            import pystray

            return pystray
        except Exception:
            return None

    def _build_icon_image(self) -> Any | None:
        try:
            from PIL import Image, ImageDraw
        except Exception:
            return None

        size = 64
        canvas = Image.new("RGBA", (size, size), (16, 14, 14, 255))
        logo_path = project_root() / "SafeDesk Logo.png"
        if logo_path.exists():
            try:
                with Image.open(logo_path) as image:
                    source = image.convert("RGBA").copy()
                resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)
                source.thumbnail((size - 8, size - 8), resample)
                offset = ((size - source.width) // 2, (size - source.height) // 2)
                canvas.alpha_composite(source, dest=offset)
                return canvas
            except Exception:
                pass

        draw = ImageDraw.Draw(canvas)
        draw.rectangle((5, 5, size - 6, size - 6), outline=(182, 29, 24, 255), width=3)
        draw.polygon(
            ((size // 2, 12), (size - 16, 25), (size - 20, 50), (size // 2, 56), (20, 50), (16, 25)),
            fill=(55, 48, 45, 255),
            outline=(214, 58, 48, 255),
        )
        draw.rectangle((25, 28, 39, 44), fill=(214, 58, 48, 255))
        return canvas

    def _run_icon(self) -> None:
        try:
            if self.icon is not None:
                self.icon.run()
        except Exception:
            self._running = False

    def _dispatch(self, callback: Callable[[], None]) -> None:
        try:
            self.dispatch_to_gui(callback)
        except Exception:
            pass

    def _menu_open_safedesk(self, _icon, _item) -> None:
        self._dispatch(self.on_open_safedesk)

    def _menu_open_admin_console(self, _icon, _item) -> None:
        self._dispatch(self.on_open_admin_console)

    def _menu_lock_safedesk(self, _icon, _item) -> None:
        self._dispatch(self.on_lock_safedesk)

    def _menu_exit_safedesk(self, _icon, _item) -> None:
        if self.allow_exit:
            self._dispatch(self.on_exit_safedesk)

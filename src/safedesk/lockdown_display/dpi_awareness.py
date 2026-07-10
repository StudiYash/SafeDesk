"""Windows DPI-awareness helper for lockdown display geometry."""

from __future__ import annotations

import sys


def enable_windows_dpi_awareness() -> bool:
    """Enable DPI-aware monitor geometry on Windows before Tk creates windows."""

    if sys.platform != "win32":
        return False

    try:
        import ctypes
    except Exception:
        return False

    try:
        result = ctypes.windll.shcore.SetProcessDpiAwareness(2)
        if result == 0 or result in (-2147024891, 2147942405):
            return True
    except Exception:
        pass

    try:
        return bool(ctypes.windll.user32.SetProcessDPIAware())
    except Exception:
        return False

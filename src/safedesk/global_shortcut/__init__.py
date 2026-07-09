"""SafeDesk global shortcut activation foundation."""

from safedesk.global_shortcut.shortcut_manager import GlobalShortcutManager
from safedesk.global_shortcut.shortcut_models import (
    GlobalShortcutStatus,
    HotkeyParseResult,
    ShortcutOperationResult,
)
from safedesk.global_shortcut.windows_hotkey_controller import WindowsHotkeyController

__all__ = [
    "GlobalShortcutManager",
    "GlobalShortcutStatus",
    "HotkeyParseResult",
    "ShortcutOperationResult",
    "WindowsHotkeyController",
]

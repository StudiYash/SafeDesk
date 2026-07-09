"""Models for the SafeDesk global shortcut foundation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HotkeyParseResult:
    """Parsed registered-hotkey values for the single Phase 20 shortcut."""

    success: bool
    status: str
    message: str
    normalized_hotkey: str = ""
    modifiers: int = 0
    virtual_key: int = 0


@dataclass(frozen=True)
class GlobalShortcutStatus:
    """Safe public status for global shortcut availability."""

    enabled: bool
    foundation_enabled: bool
    demo_only: bool
    shortcut_enabled: bool
    supported_platform: bool
    hotkey_supported: bool
    activation_action: str
    registered: bool
    available: bool
    message: str


@dataclass(frozen=True)
class ShortcutOperationResult:
    """Result for starting or stopping global shortcut registration."""

    success: bool
    status: str
    message: str
    registered: bool
    available: bool

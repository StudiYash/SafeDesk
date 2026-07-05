"""SafeDesk application mode models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SafeDeskMode(str, Enum):
    """Top-level SafeDesk application modes."""

    LAUNCH = "launch"
    ADMIN_CONSOLE = "admin_console"
    PUBLIC_LOCK = "public_lock"
    BACKGROUND_AGENT = "background_agent"


@dataclass(frozen=True)
class AppModeTransitionResult:
    """Result of a requested SafeDesk mode transition."""

    success: bool
    previous_mode: SafeDeskMode
    new_mode: SafeDeskMode
    status: str
    message: str


def parse_app_mode(value: SafeDeskMode | str | None) -> SafeDeskMode | None:
    """Parse a configured mode value without raising."""

    if isinstance(value, SafeDeskMode):
        return value
    if not isinstance(value, str):
        return None
    try:
        return SafeDeskMode(value)
    except ValueError:
        return None


def _app_mode_flag(config: dict, key: str, default: bool = True) -> bool:
    app_modes = config.get("app_modes", {}) if isinstance(config, dict) else {}
    if not isinstance(app_modes, dict):
        return default
    return app_modes.get(key, default) is True


def can_open_admin_console_from_launch(config: dict) -> bool:
    """Return whether the Launch Screen can expose the admin-console route."""

    return _app_mode_flag(config, "allow_admin_console_from_launch", True)


def can_open_public_lock_placeholder(config: dict) -> bool:
    """Return whether the public lock placeholder route is available."""

    return _app_mode_flag(config, "allow_public_lock_placeholder", True)

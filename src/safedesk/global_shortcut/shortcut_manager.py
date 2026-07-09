"""Safe configuration manager for the global shortcut foundation."""

from __future__ import annotations

import platform

from safedesk.global_shortcut.shortcut_models import GlobalShortcutStatus, HotkeyParseResult

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
VK_L = 0x4C
SUPPORTED_HOTKEY = "ctrl+alt+l"
SUPPORTED_ACTION = "public_lock"
SUPPORTED_PLATFORM = "Windows"


def normalize_hotkey(value: str) -> str:
    """Normalize a configured hotkey without processing typed input."""

    return "+".join(part.strip().lower() for part in str(value).split("+") if part.strip())


def parse_hotkey(value: str) -> HotkeyParseResult:
    """Parse the single Phase 20 registered hotkey."""

    normalized = normalize_hotkey(value)
    if normalized != SUPPORTED_HOTKEY:
        return HotkeyParseResult(
            success=False,
            status="unsupported_hotkey",
            message="Global shortcut hotkey is not supported in this phase.",
        )
    return HotkeyParseResult(
        success=True,
        status="parsed",
        message="Global shortcut hotkey is supported.",
        normalized_hotkey=SUPPORTED_HOTKEY,
        modifiers=MOD_CONTROL | MOD_ALT,
        virtual_key=VK_L,
    )


class GlobalShortcutManager:
    """Read Phase 20 global shortcut config without monitoring typed keys."""

    def __init__(self, config: dict, platform_name: str | None = None):
        self.config = config
        raw_config = config.get("global_shortcut", {}) if isinstance(config, dict) else {}
        self.shortcut_config = raw_config if isinstance(raw_config, dict) else {}
        self.platform_name = platform_name or platform.system()

    @property
    def enabled(self) -> bool:
        return self.shortcut_config.get("enabled", True) is True

    @property
    def foundation_enabled(self) -> bool:
        return self.shortcut_config.get("foundation_enabled", True) is True

    @property
    def demo_only(self) -> bool:
        return self.shortcut_config.get("demo_only", True) is True

    @property
    def shortcut_enabled(self) -> bool:
        return self.shortcut_config.get("shortcut_enabled", True) is True

    @property
    def hotkey(self) -> str:
        return str(self.shortcut_config.get("hotkey", SUPPORTED_HOTKEY))

    @property
    def activation_action(self) -> str:
        return str(self.shortcut_config.get("activation_action", SUPPORTED_ACTION))

    @property
    def require_app_running(self) -> bool:
        return self.shortcut_config.get("require_app_running", True) is True

    @property
    def allow_when_minimized_to_tray(self) -> bool:
        return self.shortcut_config.get("allow_when_minimized_to_tray", True) is True

    @property
    def allow_when_admin_console_open(self) -> bool:
        return self.shortcut_config.get("allow_when_admin_console_open", True) is True

    @property
    def allow_when_public_lock_open(self) -> bool:
        return self.shortcut_config.get("allow_when_public_lock_open", False) is True

    @property
    def supported_platforms(self) -> tuple[str, ...]:
        raw_platforms = self.shortcut_config.get("supported_platforms", (SUPPORTED_PLATFORM,))
        if not isinstance(raw_platforms, list):
            return ()
        return tuple(platform for platform in raw_platforms if isinstance(platform, str))

    def parse_hotkey(self) -> HotkeyParseResult:
        return parse_hotkey(self.hotkey)

    def is_supported_platform(self) -> bool:
        return self.platform_name in self.supported_platforms and self.platform_name == SUPPORTED_PLATFORM

    def hotkey_supported(self) -> bool:
        return self.parse_hotkey().success

    def should_attempt_registration(self) -> bool:
        """Return True only for the narrow owner-controlled registered hotkey."""

        return (
            self.enabled
            and self.foundation_enabled
            and self.demo_only
            and self.shortcut_enabled
            and self.require_app_running
            and self.activation_action == SUPPORTED_ACTION
            and self.is_supported_platform()
            and self.hotkey_supported()
        )

    def build_status(self, *, registered: bool = False, available: bool = False) -> GlobalShortcutStatus:
        """Build safe shortcut status without exposing raw OS errors."""

        hotkey_result = self.parse_hotkey()
        supported_platform = self.is_supported_platform()
        hotkey_supported = hotkey_result.success
        if not self.enabled:
            message = "Global shortcut foundation is disabled."
        elif not self.foundation_enabled:
            message = "Global shortcut foundation is not available."
        elif not self.demo_only:
            message = "Global shortcut requires demo-only mode in this phase."
        elif not self.shortcut_enabled:
            message = "Global shortcut is disabled."
        elif not self.require_app_running:
            message = "Global shortcut requires SafeDesk to be running in this phase."
        elif self.activation_action != SUPPORTED_ACTION:
            message = "Global shortcut action is not supported."
        elif not hotkey_supported:
            message = hotkey_result.message
        elif not supported_platform:
            message = "Global shortcut support is unavailable on this platform."
        elif registered:
            message = "Global shortcut is registered."
        elif available:
            message = "Global shortcut support is available."
        else:
            message = "Global shortcut support is unavailable."

        return GlobalShortcutStatus(
            enabled=self.enabled,
            foundation_enabled=self.foundation_enabled,
            demo_only=self.demo_only,
            shortcut_enabled=self.shortcut_enabled,
            supported_platform=supported_platform,
            hotkey_supported=hotkey_supported,
            activation_action=self.activation_action,
            registered=registered,
            available=available,
            message=message,
        )

"""Guard checks for optional real shutdown execution."""

from __future__ import annotations

from dataclasses import dataclass
import platform


@dataclass(frozen=True)
class ShutdownGuardCheck:
    """One safe guard check for guarded real shutdown."""

    name: str
    passed: bool
    message: str


@dataclass(frozen=True)
class ShutdownGuardReport:
    """Safe guard report for GUI display and manager decisions."""

    ready: bool
    platform_supported: bool
    checks: tuple[ShutdownGuardCheck, ...]
    message: str


def evaluate_shutdown_guards(config: dict, platform_name: str | None = None) -> ShutdownGuardReport:
    """Evaluate guarded real shutdown prerequisites without executing anything."""

    shutdown = config.get("shutdown", {})
    feature_flags = config.get("feature_flags", {})
    app = config.get("app", {})
    security_mode = config.get("security_mode", {})
    current_platform = platform_name or platform.system()
    supported_platforms = shutdown.get("real_shutdown_supported_platforms", ["Windows"])
    if not isinstance(supported_platforms, list):
        supported_platforms = []
    supported_platform_names = tuple(str(item) for item in supported_platforms if isinstance(item, str))
    platform_supported = current_platform in supported_platform_names

    phrase = shutdown.get("real_shutdown_confirmation_phrase", "")
    countdown_seconds = shutdown.get("real_shutdown_countdown_seconds", 0)
    checks = (
        ShutdownGuardCheck(
            "feature_flag_enabled",
            feature_flags.get("enable_real_shutdown") is True,
            "Feature flag for real shutdown is enabled.",
        ),
        ShutdownGuardCheck(
            "guarded_shutdown_opt_in_enabled",
            shutdown.get("allow_guarded_real_shutdown") is True,
            "Guarded real shutdown local opt-in is enabled.",
        ),
        ShutdownGuardCheck(
            "real_shutdown_enabled",
            shutdown.get("real_shutdown_enabled") is True,
            "Real shutdown flag is enabled.",
        ),
        ShutdownGuardCheck(
            "real_command_enabled",
            shutdown.get("real_shutdown_command_enabled") is True,
            "Real shutdown command flag is enabled.",
        ),
        ShutdownGuardCheck(
            "demo_shutdown_only_disabled",
            shutdown.get("demo_shutdown_only") is False,
            "Demo-only shutdown mode is disabled for the guarded real test.",
        ),
        ShutdownGuardCheck(
            "app_demo_safe_mode_disabled",
            app.get("demo_safe_mode") is False,
            "App demo/safe mode is disabled.",
        ),
        ShutdownGuardCheck(
            "security_mode_not_demo_safe",
            security_mode.get("default_mode") != "demo_safe",
            "Security mode is not demo_safe.",
        ),
        ShutdownGuardCheck(
            "manual_confirmation_required",
            shutdown.get("require_manual_confirmation") is True,
            "Manual confirmation is required.",
        ),
        ShutdownGuardCheck(
            "confirmation_phrase_required",
            shutdown.get("real_shutdown_requires_confirmation_phrase") is True,
            "Typed confirmation phrase is required.",
        ),
        ShutdownGuardCheck(
            "confirmation_phrase_configured",
            isinstance(phrase, str) and bool(phrase.strip()),
            "Confirmation phrase is configured.",
        ),
        ShutdownGuardCheck(
            "countdown_seconds_at_least_30",
            isinstance(countdown_seconds, int) and not isinstance(countdown_seconds, bool) and countdown_seconds >= 30,
            "Real shutdown countdown is at least 30 seconds.",
        ),
        ShutdownGuardCheck(
            "abort_enabled",
            shutdown.get("allow_abort_real_shutdown") is True,
            "Abort pending shutdown is enabled.",
        ),
        ShutdownGuardCheck(
            "platform_supported",
            platform_supported,
            "Current platform is supported for guarded real shutdown.",
        ),
    )
    ready = all(check.passed for check in checks)
    if ready:
        message = "Guarded real shutdown checks are ready. Manual confirmation is still required."
    else:
        message = "Guarded real shutdown is blocked until all local guards pass."
    return ShutdownGuardReport(
        ready=ready,
        platform_supported=platform_supported,
        checks=checks,
        message=message,
    )

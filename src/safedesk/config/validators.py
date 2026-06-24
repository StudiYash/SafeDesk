"""Safe configuration validation for SafeDesk."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from safedesk.config.models import (
    ConfigValidationIssue,
    ConfigValidationReport,
    EnvironmentSettings,
    SafeDeskRuntimeSettings,
)
from safedesk.storage.paths import project_root
from safedesk.utils.constants import (
    DEFAULT_ENVIRONMENT,
    PROJECT_NAME,
    PROJECT_VERSION,
    SUPPORTED_ENVIRONMENTS,
    SUPPORTED_SECURITY_MODES,
)


def _bool_config(config: dict[str, Any], section: str, key: str, default: bool = False) -> bool:
    value = config.get(section, {}).get(key, default)
    return bool(value)


def _positive_int_issue(config: dict[str, Any], path: tuple[str, str]) -> ConfigValidationIssue | None:
    section, key = path
    value = config.get(section, {}).get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return ConfigValidationIssue(
            "error",
            "invalid_positive_integer",
            f"`{section}.{key}` must be a positive integer.",
        )
    return None


def _path_issue(root: Path, key: str, raw_value: Any) -> ConfigValidationIssue | None:
    if not isinstance(raw_value, str) or not raw_value.strip():
        return ConfigValidationIssue(
            "error",
            "invalid_runtime_path",
            f"`paths.{key}` must be a non-empty relative path.",
        )

    path = Path(raw_value)
    resolved = path if path.is_absolute() else root / path
    if not resolved.exists():
        return ConfigValidationIssue(
            "warning",
            "runtime_path_missing",
            f"`paths.{key}` does not exist yet and should be created by setup before use.",
        )
    return None


def _effective_flags(config: dict[str, Any], env: EnvironmentSettings) -> tuple[bool, bool, bool]:
    feature_flags = config.get("feature_flags", {})
    shutdown = config.get("shutdown", {})
    lockdown = config.get("lockdown", {})
    privacy = config.get("privacy", {})

    real_email = bool(feature_flags.get("enable_real_email", False)) or env.enable_real_email
    real_shutdown = (
        bool(feature_flags.get("enable_real_shutdown", False))
        or bool(shutdown.get("real_shutdown_enabled", False))
        or env.enable_real_shutdown
    )
    real_lockdown = (
        bool(feature_flags.get("enable_real_lockdown", False))
        or bool(lockdown.get("real_lockdown_enabled", False))
        or env.enable_real_lockdown
    )
    return real_email, real_shutdown, real_lockdown


def validate_config(
    config: dict[str, Any],
    env: EnvironmentSettings,
    root: Path | None = None,
) -> ConfigValidationReport:
    """Validate configuration without exposing secret values."""

    issues: list[ConfigValidationIssue] = []
    base_root = root or project_root()

    app = config.get("app", {})
    environment = env.safedesk_env or app.get("environment", DEFAULT_ENVIRONMENT)
    if environment not in SUPPORTED_ENVIRONMENTS:
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_environment",
                "`SAFEDESK_ENV` or `app.environment` is not supported.",
            )
        )

    security_mode = config.get("security_mode", {}).get("default_mode")
    if security_mode not in SUPPORTED_SECURITY_MODES:
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_security_mode",
                "`security_mode.default_mode` is not supported.",
            )
        )

    available_modes = config.get("security_mode", {}).get("available_modes", [])
    if not isinstance(available_modes, list) or any(mode not in SUPPORTED_SECURITY_MODES for mode in available_modes):
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_available_modes",
                "`security_mode.available_modes` contains unsupported values.",
            )
        )

    for item in (
        ("authentication", "max_unlock_attempts"),
        ("authentication", "lockout_seconds"),
        ("otp", "code_length"),
        ("otp", "expires_seconds"),
        ("otp", "max_attempts"),
        ("threat_levels", "max_level"),
        ("threat_levels", "forceful_attempt_threshold"),
        ("shutdown", "shutdown_after_threat_level"),
        ("shutdown", "warning_seconds"),
    ):
        issue = _positive_int_issue(config, item)
        if issue:
            issues.append(issue)

    real_email, real_shutdown, real_lockdown = _effective_flags(config, env)
    demo_safe_mode = bool(app.get("demo_safe_mode", True)) or security_mode == "demo_safe"

    if real_email:
        if not env.email_sender_address:
            issues.append(ConfigValidationIssue("error", "missing_email_sender", "Real email requires an email sender address."))
        if not env.email_app_password_present:
            issues.append(ConfigValidationIssue("error", "missing_email_secret", "Real email requires an app password."))
        if not env.otp_receiver_email:
            issues.append(ConfigValidationIssue("error", "missing_otp_receiver", "Real email requires an OTP receiver email."))

    if real_shutdown:
        issues.append(ConfigValidationIssue("warning", "real_shutdown_enabled", "Real shutdown is enabled and must be reviewed before use."))

    if real_lockdown:
        issues.append(ConfigValidationIssue("warning", "real_lockdown_enabled", "Real lockdown is enabled and must be reviewed before use."))

    if demo_safe_mode and real_shutdown:
        issues.append(ConfigValidationIssue("error", "demo_real_shutdown_conflict", "Demo/safe mode cannot run with real shutdown enabled."))

    if demo_safe_mode and real_lockdown:
        issues.append(ConfigValidationIssue("error", "demo_real_lockdown_conflict", "Demo/safe mode cannot run with real lockdown enabled."))

    paths = config.get("paths", {})
    for key in ("owner_data_dir", "intruder_data_dir", "logs_dir", "cache_dir", "config_dir"):
        issue = _path_issue(base_root, key, paths.get(key))
        if issue:
            issues.append(issue)

    cloud_sync_enabled = _bool_config(config, "privacy", "cloud_sync_enabled", False)
    if cloud_sync_enabled:
        issues.append(ConfigValidationIssue("error", "cloud_sync_enabled", "Cloud sync must remain disabled by default."))

    return ConfigValidationReport(
        is_valid=not any(issue.severity == "error" for issue in issues),
        issues=tuple(issues),
    )


def build_runtime_settings(
    config: dict[str, Any],
    env: EnvironmentSettings,
    report: ConfigValidationReport,
) -> SafeDeskRuntimeSettings:
    """Build sanitized runtime settings for the startup check."""

    app = config.get("app", {})
    real_email, real_shutdown, real_lockdown = _effective_flags(config, env)
    security_mode = config.get("security_mode", {}).get("default_mode", "demo_safe")

    return SafeDeskRuntimeSettings(
        app_name=str(app.get("name", PROJECT_NAME)),
        version=str(app.get("version", PROJECT_VERSION)),
        environment=env.safedesk_env or str(app.get("environment", DEFAULT_ENVIRONMENT)),
        security_mode=str(security_mode),
        demo_safe_mode=bool(app.get("demo_safe_mode", True)) or security_mode == "demo_safe",
        real_email_enabled=real_email,
        real_shutdown_enabled=real_shutdown,
        real_lockdown_enabled=real_lockdown,
        validation_report=report,
    )

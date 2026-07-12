"""Safe configuration validation for SafeDesk."""

from __future__ import annotations

from pathlib import Path, PureWindowsPath
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

SUPPORTED_UI_THEMES = ("dark", "light", "system")
SUPPORTED_OWNER_SAMPLE_FORMATS = ("jpg", "png")
SUPPORTED_RECOGNITION_METRICS = ("cosine", "euclidean", "euclidean_l2")
SUPPORTED_AUTH_HASH_ALGORITHMS = ("pbkdf2_sha256",)
SUPPORTED_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")
SUPPORTED_LOG_DB_SUFFIXES = (".sqlite", ".sqlite3", ".db")
SUPPORTED_INTRUDER_IMAGE_FORMATS = ("jpg", "png")
SUPPORTED_APP_DEFAULT_START_MODES = ("launch", "admin_gate", "admin_console", "public_lock")
SUPPORTED_GLOBAL_SHORTCUT_HOTKEYS = ("ctrl+alt+l",)
SUPPORTED_GLOBAL_SHORTCUT_ACTIONS = ("public_lock",)
SUPPORTED_GLOBAL_SHORTCUT_PLATFORMS = ("Windows",)


def is_basic_email(value: str) -> bool:
    """Return True when value looks like a basic email address."""

    if "@" not in value:
        return False
    _, domain = value.rsplit("@", 1)
    return "." in domain and bool(domain.split(".", 1)[0]) and bool(domain.rsplit(".", 1)[-1])


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


def _non_negative_int_issue(config: dict[str, Any], path: tuple[str, str]) -> ConfigValidationIssue | None:
    section, key = path
    value = config.get(section, {}).get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return ConfigValidationIssue(
            "error",
            "invalid_non_negative_integer",
            f"`{section}.{key}` must be zero or a positive integer.",
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


def _non_empty_string_issue(section: str, key: str, value: Any) -> ConfigValidationIssue | None:
    if not isinstance(value, str) or not value.strip():
        return ConfigValidationIssue(
            "error",
            "invalid_non_empty_string",
            f"`{section}.{key}` must be a non-empty string.",
        )
    return None


def _number_range_issue(
    section: str,
    key: str,
    value: Any,
    minimum: float,
    maximum: float,
) -> ConfigValidationIssue | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not minimum <= float(value) <= maximum:
        return ConfigValidationIssue(
            "error",
            "invalid_number_range",
            f"`{section}.{key}` must be a number between {minimum} and {maximum}.",
        )
    return None


def _relative_path_issue(section: str, key: str, value: Any) -> ConfigValidationIssue | None:
    if not isinstance(value, str) or not value.strip():
        return ConfigValidationIssue(
            "error",
            "invalid_relative_path",
            f"`{section}.{key}` must be a non-empty relative path.",
        )
    if Path(value).is_absolute():
        return ConfigValidationIssue(
            "error",
            "absolute_relative_path",
            f"`{section}.{key}` must remain relative to the SafeDesk project root.",
        )
    return None


def _is_absolute_path_text(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return Path(normalized).is_absolute() or PureWindowsPath(value).is_absolute() or normalized.startswith("//")


def _relative_parts(value: str) -> tuple[str, ...]:
    return tuple(part for part in value.replace("\\", "/").split("/") if part not in {"", "."})


def _effective_flags(config: dict[str, Any], env: EnvironmentSettings) -> tuple[bool, bool, bool]:
    feature_flags = config.get("feature_flags", {})
    shutdown = config.get("shutdown", {})
    lockdown = config.get("lockdown", {})

    real_email = bool(feature_flags.get("enable_real_email", False)) or env.enable_real_email
    real_shutdown = (
        bool(feature_flags.get("enable_real_shutdown", False))
        or bool(shutdown.get("real_shutdown_enabled", False))
        or bool(shutdown.get("real_shutdown_command_enabled", False))
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

    setup = config.get("setup", {})
    setup_completed = setup.get("completed", False)
    if not isinstance(setup_completed, bool):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_setup_completed",
                "`setup.completed` must be a boolean.",
            )
        )
        setup_completed = False

    setup_version_issue = _positive_int_issue(config, ("setup", "setup_version"))
    if setup_version_issue:
        issues.append(setup_version_issue)

    for key in ("completed_at", "last_updated_at"):
        if not isinstance(setup.get(key, ""), str):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_setup_timestamp",
                    f"`setup.{key}` must be a string.",
                )
            )

    owner_profile = config.get("owner_profile", {})
    owner_name = owner_profile.get("owner_name", "")
    owner_email = owner_profile.get("owner_email", "")
    if not isinstance(owner_name, str):
        issues.append(ConfigValidationIssue("error", "invalid_owner_name", "`owner_profile.owner_name` must be a string."))
        owner_name = ""
    if not isinstance(owner_email, str):
        issues.append(ConfigValidationIssue("error", "invalid_owner_email", "`owner_profile.owner_email` must be a string."))
        owner_email = ""
    if setup_completed and not owner_name.strip():
        issues.append(
            ConfigValidationIssue(
                "error",
                "missing_setup_owner_name",
                "Completed setup requires an owner display name.",
            )
        )
    if owner_email.strip() and not is_basic_email(owner_email.strip()):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_owner_email_format",
                "`owner_profile.owner_email` must use a basic email format when provided.",
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

    app_modes = config.get("app_modes", {})
    if not isinstance(app_modes, dict):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_app_modes_section",
                "`app_modes` must be a configuration object.",
            )
        )
        app_modes = {}
    default_start_mode = app_modes.get("default_start_mode")
    if default_start_mode not in SUPPORTED_APP_DEFAULT_START_MODES:
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_app_default_start_mode",
                "`app_modes.default_start_mode` must be launch, admin_gate, admin_console, or public_lock.",
            )
        )

    for key in ("allow_public_lock_placeholder", "allow_admin_console_from_launch"):
        if not isinstance(app_modes.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_app_modes_boolean",
                    f"`app_modes.{key}` must be a boolean.",
                )
            )

    admin_gate = config.get("admin_gate", {})
    if not isinstance(admin_gate, dict):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_admin_gate_section",
                "`admin_gate` must be a configuration object.",
            )
        )
        admin_gate = {}

    for key in (
        "enabled",
        "foundation_enabled",
        "demo_only",
        "require_password_if_configured",
        "allow_development_continue_if_unconfigured",
    ):
        if not isinstance(admin_gate.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_admin_gate_boolean",
                    f"`admin_gate.{key}` must be a boolean.",
                )
            )

    admin_gate_max_attempts = admin_gate.get("max_attempts")
    if isinstance(admin_gate_max_attempts, bool) or not isinstance(admin_gate_max_attempts, int) or admin_gate_max_attempts < 1:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_admin_gate_max_attempts",
                "`admin_gate.max_attempts` must be an integer greater than or equal to 1.",
            )
        )

    admin_gate_lockout_seconds = admin_gate.get("lockout_seconds")
    if (
        isinstance(admin_gate_lockout_seconds, bool)
        or not isinstance(admin_gate_lockout_seconds, int)
        or admin_gate_lockout_seconds < 0
    ):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_admin_gate_lockout_seconds",
                "`admin_gate.lockout_seconds` must be zero or a positive integer.",
            )
        )

    background_agent = config.get("background_agent", {})
    if not isinstance(background_agent, dict):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_background_agent_section",
                "`background_agent` must be a configuration object.",
            )
        )
        background_agent = {}

    for key in (
        "enabled",
        "foundation_enabled",
        "demo_only",
        "system_tray_enabled",
        "minimize_to_tray",
        "close_to_tray",
        "allow_exit_from_tray",
        "show_tray_notifications",
    ):
        if not isinstance(background_agent.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_background_agent_boolean",
                    f"`background_agent.{key}` must be a boolean.",
                )
            )

    if background_agent.get("demo_only") is False:
        issues.append(
            ConfigValidationIssue(
                "error",
                "background_agent_demo_only_required",
                "`background_agent.demo_only` must remain true in Phase 19.",
            )
        )

    if background_agent.get("show_tray_notifications") is True:
        issues.append(
            ConfigValidationIssue(
                "error",
                "background_agent_notifications_disabled",
                "`background_agent.show_tray_notifications` must remain false in Phase 19.",
            )
        )

    global_shortcut = config.get("global_shortcut", {})
    if not isinstance(global_shortcut, dict):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_global_shortcut_section",
                "`global_shortcut` must be a configuration object.",
            )
        )
        global_shortcut = {}

    for key in (
        "enabled",
        "foundation_enabled",
        "demo_only",
        "shortcut_enabled",
        "require_app_running",
        "allow_when_minimized_to_tray",
        "allow_when_admin_console_open",
        "allow_when_public_lock_open",
    ):
        if not isinstance(global_shortcut.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_global_shortcut_boolean",
                    f"`global_shortcut.{key}` must be a boolean.",
                )
            )

    if global_shortcut.get("demo_only") is False:
        issues.append(
            ConfigValidationIssue(
                "error",
                "global_shortcut_demo_only_required",
                "`global_shortcut.demo_only` must remain true in Phase 20.",
            )
        )

    if global_shortcut.get("require_app_running") is False:
        issues.append(
            ConfigValidationIssue(
                "error",
                "global_shortcut_require_app_running",
                "`global_shortcut.require_app_running` must remain true in Phase 20.",
            )
        )

    hotkey = global_shortcut.get("hotkey")
    normalized_hotkey = "".join(str(hotkey).lower().split()) if isinstance(hotkey, str) else ""
    if normalized_hotkey not in SUPPORTED_GLOBAL_SHORTCUT_HOTKEYS:
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_global_shortcut_hotkey",
                "`global_shortcut.hotkey` must be ctrl+alt+l in Phase 20.",
            )
        )

    if global_shortcut.get("activation_action") not in SUPPORTED_GLOBAL_SHORTCUT_ACTIONS:
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_global_shortcut_action",
                "`global_shortcut.activation_action` must be public_lock in Phase 20.",
            )
        )

    shortcut_platforms = global_shortcut.get("supported_platforms")
    if not isinstance(shortcut_platforms, list) or not shortcut_platforms:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_global_shortcut_platforms",
                "`global_shortcut.supported_platforms` must be a non-empty list of strings.",
            )
        )
    elif any(not isinstance(platform, str) or not platform.strip() for platform in shortcut_platforms):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_global_shortcut_platforms",
                "`global_shortcut.supported_platforms` must contain only non-empty strings.",
            )
        )
    elif any(platform not in SUPPORTED_GLOBAL_SHORTCUT_PLATFORMS for platform in shortcut_platforms):
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_global_shortcut_platform",
                "`global_shortcut.supported_platforms` may only include Windows in Phase 20.",
            )
        )

    lockdown_display = config.get("lockdown_display", {})
    if not isinstance(lockdown_display, dict):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_lockdown_display_section",
                "`lockdown_display` must be a configuration object.",
            )
        )
        lockdown_display = {}

    for key in (
        "enabled",
        "foundation_enabled",
        "demo_only",
        "fullscreen_enabled",
        "multi_display_enabled",
        "borderless_enabled",
        "topmost_enabled",
        "primary_display_required",
        "fallback_to_primary_display",
        "allow_development_escape",
    ):
        if not isinstance(lockdown_display.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_lockdown_display_boolean",
                    f"`lockdown_display.{key}` must be a boolean.",
                )
            )

    if lockdown_display.get("demo_only") is False:
        issues.append(
            ConfigValidationIssue(
                "error",
                "lockdown_display_demo_only_required",
                "`lockdown_display.demo_only` must remain true in Phase 21.",
            )
        )

    escape_timeout = lockdown_display.get("development_escape_timeout_seconds")
    if isinstance(escape_timeout, bool) or not isinstance(escape_timeout, int) or not 5 <= escape_timeout <= 300:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_lockdown_display_escape_timeout",
                "`lockdown_display.development_escape_timeout_seconds` must be an integer between 5 and 300.",
            )
        )

    max_display_windows = lockdown_display.get("max_display_windows")
    if isinstance(max_display_windows, bool) or not isinstance(max_display_windows, int) or not 1 <= max_display_windows <= 8:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_lockdown_display_max_windows",
                "`lockdown_display.max_display_windows` must be an integer between 1 and 8.",
            )
        )

    safe_interaction_lock = config.get("safe_interaction_lock", {})
    if not isinstance(safe_interaction_lock, dict):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_safe_interaction_lock_section",
                "`safe_interaction_lock` must be a configuration object.",
            )
        )
        safe_interaction_lock = {}

    for key in (
        "enabled",
        "foundation_enabled",
        "demo_only",
        "focus_recovery_enabled",
        "lift_windows_on_recovery",
        "reapply_topmost_on_recovery",
        "focus_primary_on_activation",
        "focus_primary_on_recovery",
        "cleanup_on_route_change",
        "prevent_duplicate_activation",
        "log_lifecycle_events",
    ):
        if not isinstance(safe_interaction_lock.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_safe_interaction_lock_boolean",
                    f"`safe_interaction_lock.{key}` must be a boolean.",
                )
            )

    if safe_interaction_lock.get("demo_only") is False:
        issues.append(
            ConfigValidationIssue(
                "error",
                "safe_interaction_lock_demo_only_required",
                "`safe_interaction_lock.demo_only` must remain true in Phase 22.",
            )
        )

    recovery_interval = safe_interaction_lock.get("focus_recovery_interval_seconds")
    if isinstance(recovery_interval, bool) or not isinstance(recovery_interval, (int, float)) or not 1 <= float(recovery_interval) <= 10:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_safe_interaction_lock_interval",
                "`safe_interaction_lock.focus_recovery_interval_seconds` must be a number between 1 and 10.",
            )
        )

    alarm = config.get("alarm", {})
    if not isinstance(alarm, dict):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_alarm_section",
                "`alarm` must be a configuration object.",
            )
        )
        alarm = {}

    for key in (
        "enabled",
        "foundation_enabled",
        "demo_only",
        "manual_preview_enabled",
        "automatic_trigger_enabled",
        "allow_looping",
        "beep_fallback_enabled",
    ):
        if not isinstance(alarm.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_alarm_boolean",
                    f"`alarm.{key}` must be a boolean.",
                )
            )

    for key, required_value, code, message in (
        ("enabled", False, "alarm_real_enablement_disabled", "`alarm.enabled` must remain false in Phase 24."),
        ("demo_only", True, "alarm_demo_only_required", "`alarm.demo_only` must remain true in Phase 24."),
        (
            "automatic_trigger_enabled",
            False,
            "alarm_automatic_trigger_disabled",
            "`alarm.automatic_trigger_enabled` must remain false in Phase 24.",
        ),
        ("allow_looping", False, "alarm_looping_disabled", "`alarm.allow_looping` must remain false in Phase 24."),
    ):
        if alarm.get(key) is not required_value:
            issues.append(ConfigValidationIssue("error", code, message))

    preview_duration = alarm.get("max_preview_duration_seconds")
    if isinstance(preview_duration, bool) or not isinstance(preview_duration, int) or not 1 <= preview_duration <= 10:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_alarm_preview_duration",
                "`alarm.max_preview_duration_seconds` must be an integer between 1 and 10.",
            )
        )

    volume_issue = _number_range_issue("alarm", "volume", alarm.get("volume"), 0.0, 1.0)
    if volume_issue:
        issues.append(volume_issue)

    allowed_audio_dir = alarm.get("allowed_audio_dir")
    if not isinstance(allowed_audio_dir, str) or not allowed_audio_dir.strip():
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_alarm_audio_directory",
                "`alarm.allowed_audio_dir` must be a non-empty relative directory.",
            )
        )
    elif (
        _is_absolute_path_text(allowed_audio_dir)
        or ".." in _relative_parts(allowed_audio_dir)
        or not _relative_parts(allowed_audio_dir)
    ):
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsafe_alarm_audio_directory",
                "`alarm.allowed_audio_dir` must remain a relative directory without traversal.",
            )
        )

    audio_file = alarm.get("audio_file")
    if not isinstance(audio_file, str):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_alarm_audio_file",
                "`alarm.audio_file` must be a string.",
            )
        )
    elif audio_file.strip():
        audio_parts = _relative_parts(audio_file)
        if _is_absolute_path_text(audio_file) or ".." in audio_parts:
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "unsafe_alarm_audio_file",
                    "`alarm.audio_file` must remain beneath the configured audio directory.",
                )
            )
        elif Path(audio_file.replace("\\", "/")).suffix.lower() != ".wav":
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "unsupported_alarm_audio_file",
                    "`alarm.audio_file` must use the .wav extension.",
                )
            )
    threat_levels = config.get("threat_levels", {})
    for key in ("enabled", "foundation_enabled", "demo_only"):
        if not isinstance(threat_levels.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_threat_levels_boolean",
                    f"`threat_levels.{key}` must be a boolean.",
                )
            )

    if threat_levels.get("enabled") is True:
        issues.append(
            ConfigValidationIssue(
                "error",
                "threat_levels_enabled_must_remain_false",
                "`threat_levels.enabled` must remain false until automatic threat handling is connected.",
            )
        )

    if threat_levels.get("demo_only") is False:
        issues.append(
            ConfigValidationIssue(
                "error",
                "threat_levels_demo_only_required",
                "`threat_levels.demo_only` must remain true in Phase 13.",
            )
        )

    max_level = threat_levels.get("max_level")
    if isinstance(max_level, bool) or not isinstance(max_level, int) or max_level <= 0:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_threat_levels_max_level",
                "`threat_levels.max_level` must be a positive integer.",
            )
        )
        max_level = 5
    elif max_level != 5:
        issues.append(
            ConfigValidationIssue(
                "error",
                "threat_levels_max_level_required",
                "`threat_levels.max_level` must remain 5 in Phase 13.",
            )
        )

    initial_level = threat_levels.get("initial_level")
    if isinstance(initial_level, bool) or not isinstance(initial_level, int) or not 0 <= initial_level <= int(max_level):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_threat_levels_initial_level",
                "`threat_levels.initial_level` must be an integer from 0 to `threat_levels.max_level`.",
            )
        )

    for key in (
        "forceful_attempt_threshold",
        "repeated_unknown_threshold",
        "failed_password_threshold",
        "failed_otp_threshold",
        "forced_exit_threshold",
    ):
        issue = _positive_int_issue(config, ("threat_levels", key))
        if issue:
            issues.append(issue)

    threat_state_path_issue = _relative_path_issue("threat_levels", "state_path", threat_levels.get("state_path"))
    if threat_state_path_issue:
        issues.append(threat_state_path_issue)

    protected_mode = config.get("protected_mode", {})
    for key in (
        "enabled",
        "foundation_enabled",
        "demo_only",
        "allow_manual_arm",
        "allow_manual_activation",
        "allow_manual_recovery",
        "link_threat_level_demo",
    ):
        if not isinstance(protected_mode.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_protected_mode_boolean",
                    f"`protected_mode.{key}` must be a boolean.",
                )
            )

    if protected_mode.get("enabled") is True:
        issues.append(
            ConfigValidationIssue(
                "error",
                "protected_mode_enabled_must_remain_false",
                "`protected_mode.enabled` must remain false until real protected enforcement is connected.",
            )
        )

    if protected_mode.get("demo_only") is False:
        issues.append(
            ConfigValidationIssue(
                "error",
                "protected_mode_demo_only_required",
                "`protected_mode.demo_only` must remain true in Phase 14.",
            )
        )

    protected_state_path_issue = _relative_path_issue("protected_mode", "state_path", protected_mode.get("state_path"))
    if protected_state_path_issue:
        issues.append(protected_state_path_issue)

    protected_activation_level = protected_mode.get("activation_candidate_threat_level")
    protected_shutdown_level = protected_mode.get("shutdown_candidate_threat_level")
    for key, value in (
        ("activation_candidate_threat_level", protected_activation_level),
        ("shutdown_candidate_threat_level", protected_shutdown_level),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 5:
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_protected_mode_candidate_level",
                    f"`protected_mode.{key}` must be an integer from 0 to 5.",
                )
            )

    if (
        isinstance(protected_activation_level, int)
        and not isinstance(protected_activation_level, bool)
        and isinstance(protected_shutdown_level, int)
        and not isinstance(protected_shutdown_level, bool)
        and protected_shutdown_level < protected_activation_level
    ):
        issues.append(
            ConfigValidationIssue(
                "error",
                "protected_mode_candidate_order_invalid",
                "`protected_mode.shutdown_candidate_threat_level` must be greater than or equal to `protected_mode.activation_candidate_threat_level`.",
            )
        )

    shutdown = config.get("shutdown", {})
    for key in (
        "foundation_enabled",
        "real_shutdown_enabled",
        "demo_shutdown_only",
        "real_shutdown_command_enabled",
        "allow_demo_countdown",
        "allow_cancel",
        "allow_recovery_cancel",
        "require_manual_confirmation",
        "link_threat_level_demo",
        "link_protected_mode_demo",
        "allow_guarded_real_shutdown",
        "allow_abort_real_shutdown",
        "real_shutdown_requires_confirmation_phrase",
    ):
        if not isinstance(shutdown.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_shutdown_boolean",
                    f"`shutdown.{key}` must be a boolean.",
                )
            )

    shutdown_supported_platforms = shutdown.get("real_shutdown_supported_platforms")
    if not isinstance(shutdown_supported_platforms, list) or not shutdown_supported_platforms:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_shutdown_supported_platforms",
                "`shutdown.real_shutdown_supported_platforms` must be a non-empty list of strings.",
            )
        )
    elif any(not isinstance(platform, str) or not platform.strip() for platform in shutdown_supported_platforms):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_shutdown_supported_platforms",
                "`shutdown.real_shutdown_supported_platforms` must contain only non-empty strings.",
            )
        )
    elif any(platform != "Windows" for platform in shutdown_supported_platforms):
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_shutdown_platform",
                "`shutdown.real_shutdown_supported_platforms` may only include Windows in Phase 15.",
            )
        )

    shutdown_state_path_issue = _relative_path_issue("shutdown", "state_path", shutdown.get("state_path"))
    if shutdown_state_path_issue:
        issues.append(shutdown_state_path_issue)

    shutdown_after_threat_level = shutdown.get("shutdown_after_threat_level")
    if (
        isinstance(shutdown_after_threat_level, bool)
        or not isinstance(shutdown_after_threat_level, int)
        or not 0 <= shutdown_after_threat_level <= 5
    ):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_shutdown_after_threat_level",
                "`shutdown.shutdown_after_threat_level` must be an integer from 0 to 5.",
            )
        )

    for key in ("warning_seconds", "countdown_seconds", "real_shutdown_countdown_seconds"):
        issue = _positive_int_issue(config, ("shutdown", key))
        if issue:
            issues.append(issue)

    real_shutdown_countdown_seconds = shutdown.get("real_shutdown_countdown_seconds")
    if (
        isinstance(real_shutdown_countdown_seconds, int)
        and not isinstance(real_shutdown_countdown_seconds, bool)
        and real_shutdown_countdown_seconds < 30
    ):
        issues.append(
            ConfigValidationIssue(
                "error",
                "shutdown_real_countdown_too_short",
                "`shutdown.real_shutdown_countdown_seconds` must be at least 30.",
            )
        )

    shutdown_confirmation_phrase = shutdown.get("real_shutdown_confirmation_phrase")
    if not isinstance(shutdown_confirmation_phrase, str) or not shutdown_confirmation_phrase.strip():
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_shutdown_confirmation_phrase",
                "`shutdown.real_shutdown_confirmation_phrase` must be a non-empty string.",
            )
        )

    real_guard_flags = {
        "feature_flags.enable_real_shutdown": config.get("feature_flags", {}).get("enable_real_shutdown", False) is True,
        "shutdown.allow_guarded_real_shutdown": shutdown.get("allow_guarded_real_shutdown") is True,
        "shutdown.real_shutdown_enabled": shutdown.get("real_shutdown_enabled") is True,
        "shutdown.real_shutdown_command_enabled": shutdown.get("real_shutdown_command_enabled") is True,
        "shutdown.demo_shutdown_only_disabled": shutdown.get("demo_shutdown_only") is False,
        "app.demo_safe_mode_disabled": app.get("demo_safe_mode") is False,
        "security_mode.not_demo_safe": security_mode != "demo_safe",
        "shutdown.require_manual_confirmation": shutdown.get("require_manual_confirmation") is True,
        "shutdown.real_shutdown_requires_confirmation_phrase": shutdown.get("real_shutdown_requires_confirmation_phrase") is True,
        "shutdown.confirmation_phrase_configured": isinstance(shutdown_confirmation_phrase, str) and bool(shutdown_confirmation_phrase.strip()),
        "shutdown.real_shutdown_countdown_at_least_30": isinstance(real_shutdown_countdown_seconds, int)
        and not isinstance(real_shutdown_countdown_seconds, bool)
        and real_shutdown_countdown_seconds >= 30,
        "shutdown.allow_abort_real_shutdown": shutdown.get("allow_abort_real_shutdown") is True,
    }
    hard_real_flags = (
        shutdown.get("allow_guarded_real_shutdown") is True
        or shutdown.get("real_shutdown_enabled") is True
        or shutdown.get("real_shutdown_command_enabled") is True
        or shutdown.get("demo_shutdown_only") is False
        or config.get("feature_flags", {}).get("enable_real_shutdown") is True
    )
    if hard_real_flags and app.get("demo_safe_mode") is True:
        issues.append(
            ConfigValidationIssue(
                "error",
                "shutdown_demo_safe_mode_conflict",
                "Demo/safe mode cannot run with guarded real shutdown flags enabled.",
            )
        )
    if (shutdown.get("real_shutdown_enabled") is True or shutdown.get("real_shutdown_command_enabled") is True) and (
        config.get("feature_flags", {}).get("enable_real_shutdown") is not True
    ):
        issues.append(
            ConfigValidationIssue(
                "error",
                "shutdown_feature_flag_required",
                "`feature_flags.enable_real_shutdown` must be true before real shutdown flags can be enabled.",
            )
        )
    if hard_real_flags and not all(real_guard_flags.values()):
        missing = ", ".join(key for key, enabled in real_guard_flags.items() if not enabled)
        issues.append(
            ConfigValidationIssue(
                "error",
                "incomplete_real_shutdown_guards",
                f"Guarded real shutdown requires all safety guards before validation can pass. Missing: {missing}.",
            )
        )

    for item in (
        ("ui", "window_width"),
        ("ui", "window_height"),
        ("ui", "minimum_width"),
        ("ui", "minimum_height"),
    ):
        issue = _positive_int_issue(config, item)
        if issue:
            issues.append(issue)

    otp = config.get("otp", {})
    for key in ("enabled", "otp_foundation_enabled", "demo_only"):
        if not isinstance(otp.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_otp_boolean",
                    f"`otp.{key}` must be a boolean.",
                )
            )

    if otp.get("demo_only") is False:
        issues.append(
            ConfigValidationIssue(
                "error",
                "otp_demo_only_required",
                "`otp.demo_only` must remain true in Phase 10.",
            )
        )

    if otp.get("enabled") is True:
        issues.append(
            ConfigValidationIssue(
                "error",
                "otp_final_auth_not_connected",
                "`otp.enabled` must remain false until protected-mode OTP authentication is connected.",
            )
        )

    if otp.get("delivery_method") != "email":
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_otp_delivery_method",
                "`otp.delivery_method` must be email in Phase 10.",
            )
        )

    for item in (
        ("otp", "code_length"),
        ("otp", "expires_seconds"),
        ("otp", "max_attempts"),
        ("otp", "resend_limit"),
    ):
        issue = _positive_int_issue(config, item)
        if issue:
            issues.append(issue)

    resend_cooldown_issue = _non_negative_int_issue(config, ("otp", "resend_cooldown_seconds"))
    if resend_cooldown_issue:
        issues.append(resend_cooldown_issue)

    email = config.get("email", {})
    issue = _non_empty_string_issue("email", "smtp_host", email.get("smtp_host"))
    if issue:
        issues.append(issue)

    smtp_port_issue = _positive_int_issue(config, ("email", "smtp_port"))
    if smtp_port_issue:
        issues.append(smtp_port_issue)

    timeout_issue = _positive_int_issue(config, ("email", "timeout_seconds"))
    if timeout_issue:
        issues.append(timeout_issue)

    sender_name_issue = _non_empty_string_issue("email", "sender_display_name", email.get("sender_display_name"))
    if sender_name_issue:
        issues.append(sender_name_issue)

    for key in ("use_tls", "demo_only"):
        if not isinstance(email.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_email_boolean",
                    f"`email.{key}` must be a boolean.",
                )
            )

    authentication = config.get("authentication", {})
    for key in ("password_fallback_enabled", "panic_code_enabled", "auth_foundation_enabled", "demo_only"):
        if not isinstance(authentication.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_authentication_boolean",
                    f"`authentication.{key}` must be a boolean.",
                )
            )

    if authentication.get("demo_only") is False:
        issues.append(
            ConfigValidationIssue(
                "error",
                "authentication_demo_only_required",
                "`authentication.demo_only` must remain true in Phase 9.",
            )
        )

    if authentication.get("password_fallback_enabled") is True:
        issues.append(
            ConfigValidationIssue(
                "error",
                "password_fallback_not_connected",
                "`authentication.password_fallback_enabled` must remain false until protected-mode authentication is connected.",
            )
        )

    if authentication.get("panic_code_enabled") is True:
        issues.append(
            ConfigValidationIssue(
                "error",
                "panic_code_not_connected",
                "`authentication.panic_code_enabled` must remain false until protected-mode recovery authentication is connected.",
            )
        )

    secrets_path = authentication.get("secrets_path")
    if not isinstance(secrets_path, str) or not secrets_path.strip():
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_authentication_secrets_path",
                "`authentication.secrets_path` must be a non-empty relative path.",
            )
        )
    elif Path(secrets_path).is_absolute():
        issues.append(
            ConfigValidationIssue(
                "error",
                "absolute_authentication_secrets_path",
                "`authentication.secrets_path` must remain relative to the SafeDesk project root.",
            )
        )

    if authentication.get("hash_algorithm") not in SUPPORTED_AUTH_HASH_ALGORITHMS:
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_authentication_hash_algorithm",
                "`authentication.hash_algorithm` must be pbkdf2_sha256.",
            )
        )

    for item in (
        ("authentication", "pbkdf2_iterations"),
        ("authentication", "minimum_password_length"),
        ("authentication", "minimum_panic_code_length"),
        ("authentication", "max_unlock_attempts"),
        ("authentication", "lockout_seconds"),
    ):
        issue = _positive_int_issue(config, item)
        if issue:
            issues.append(issue)

    recovery_codes = config.get("recovery_codes", {})
    if not isinstance(recovery_codes, dict):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_recovery_codes_section",
                "`recovery_codes` must be a configuration object.",
            )
        )
        recovery_codes = {}

    for key in ("enabled", "foundation_enabled", "demo_only", "single_use"):
        if not isinstance(recovery_codes.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_recovery_codes_boolean",
                    f"`recovery_codes.{key}` must be a boolean.",
                )
            )

    if recovery_codes.get("demo_only") is False:
        issues.append(
            ConfigValidationIssue(
                "error",
                "recovery_codes_demo_only_required",
                "`recovery_codes.demo_only` must remain true in Phase 18.1.",
            )
        )

    recovery_code_count = recovery_codes.get("code_count")
    if isinstance(recovery_code_count, bool) or not isinstance(recovery_code_count, int) or not 1 <= recovery_code_count <= 20:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_recovery_code_count",
                "`recovery_codes.code_count` must be an integer between 1 and 20.",
            )
        )

    recovery_code_length = recovery_codes.get("code_length")
    if isinstance(recovery_code_length, bool) or not isinstance(recovery_code_length, int) or recovery_code_length != 16:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_recovery_code_length",
                "`recovery_codes.code_length` must be exactly 16 in Phase 18.1.",
            )
        )

    recovery_special_characters = recovery_codes.get("allowed_special_characters")
    if not isinstance(recovery_special_characters, str) or not recovery_special_characters:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_recovery_special_characters",
                "`recovery_codes.allowed_special_characters` must be a non-empty string.",
            )
        )
    elif any(character.isspace() for character in recovery_special_characters):
        issues.append(
            ConfigValidationIssue(
                "error",
                "recovery_special_characters_whitespace",
                "`recovery_codes.allowed_special_characters` must not contain whitespace.",
            )
        )

    logging_config = config.get("logging", {})
    for key in ("enabled", "demo_only"):
        if not isinstance(logging_config.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_logging_boolean",
                    f"`logging.{key}` must be a boolean.",
                )
            )

    if logging_config.get("demo_only") is False:
        issues.append(
            ConfigValidationIssue(
                "error",
                "logging_demo_only_required",
                "`logging.demo_only` must remain true in Phase 11.",
            )
        )

    database_path = logging_config.get("database_path")
    if not isinstance(database_path, str) or not database_path.strip():
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_logging_database_path",
                "`logging.database_path` must be a non-empty relative path.",
            )
        )
    else:
        log_path = Path(database_path)
        if log_path.is_absolute():
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "absolute_logging_database_path",
                    "`logging.database_path` must remain relative to the SafeDesk project root.",
                )
            )
        if log_path.suffix.lower() not in SUPPORTED_LOG_DB_SUFFIXES:
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_logging_database_extension",
                    "`logging.database_path` must end with .sqlite, .sqlite3, or .db.",
                )
            )

    if logging_config.get("log_level") not in SUPPORTED_LOG_LEVELS:
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_logging_level",
                "`logging.log_level` must be DEBUG, INFO, WARNING, or ERROR.",
            )
        )

    for item in (
        ("logging", "max_recent_events"),
        ("logging", "retention_days"),
    ):
        issue = _positive_int_issue(config, item)
        if issue:
            issues.append(issue)

    ui = config.get("ui", {})
    theme = ui.get("theme")
    if theme not in SUPPORTED_UI_THEMES:
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_ui_theme",
                "`ui.theme` must be one of dark, light, or system.",
            )
        )

    color_theme = ui.get("color_theme")
    if not isinstance(color_theme, str) or not color_theme.strip():
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_ui_color_theme",
                "`ui.color_theme` must be a non-empty string.",
            )
        )

    owner_registration = config.get("owner_face_registration", {})
    if not isinstance(owner_registration.get("enabled", True), bool):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_owner_registration_enabled",
                "`owner_face_registration.enabled` must be a boolean.",
            )
        )

    for item in (
        ("owner_face_registration", "required_samples"),
        ("owner_face_registration", "image_quality"),
    ):
        issue = _positive_int_issue(config, item)
        if issue:
            issues.append(issue)

    camera_index = owner_registration.get("camera_index")
    if isinstance(camera_index, bool) or not isinstance(camera_index, int) or camera_index < 0:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_owner_registration_camera_index",
                "`owner_face_registration.camera_index` must be zero or a positive integer.",
            )
        )

    for key in ("samples_dir", "manifest_path"):
        issue = _non_empty_string_issue("owner_face_registration", key, owner_registration.get(key))
        if issue:
            issues.append(issue)

    image_format = owner_registration.get("image_format")
    if image_format not in SUPPORTED_OWNER_SAMPLE_FORMATS:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_owner_registration_image_format",
                "`owner_face_registration.image_format` must be jpg or png.",
            )
        )

    image_quality = owner_registration.get("image_quality")
    if isinstance(image_quality, int) and not isinstance(image_quality, bool) and not 1 <= image_quality <= 100:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_owner_registration_image_quality",
                "`owner_face_registration.image_quality` must be between 1 and 100.",
            )
        )

    face_recognition_enabled = bool(config.get("face_recognition", {}).get("enabled", False))
    if face_recognition_enabled:
        issues.append(
            ConfigValidationIssue(
                "error",
                "final_face_recognition_auth_disabled",
                "`face_recognition.enabled` must remain false for the demo foundation.",
            )
        )

    owner_recognition = config.get("owner_recognition", {})
    if not isinstance(owner_recognition.get("enabled", True), bool):
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_owner_recognition_enabled",
                "`owner_recognition.enabled` must be a boolean.",
            )
        )

    for key in ("model_name", "detector_backend", "profile_path", "cache_dir"):
        issue = _non_empty_string_issue("owner_recognition", key, owner_recognition.get(key))
        if issue:
            issues.append(issue)

    if owner_recognition.get("model_name") != "ArcFace":
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_owner_recognition_model",
                "`owner_recognition.model_name` must be ArcFace in this phase.",
            )
        )

    if owner_recognition.get("detector_backend") != "retinaface":
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_owner_recognition_detector",
                "`owner_recognition.detector_backend` must be retinaface in this phase.",
            )
        )

    if owner_recognition.get("distance_metric") not in SUPPORTED_RECOGNITION_METRICS:
        issues.append(
            ConfigValidationIssue(
                "error",
                "unsupported_owner_recognition_metric",
                "`owner_recognition.distance_metric` must be cosine, euclidean, or euclidean_l2.",
            )
        )

    for key in ("align", "enforce_detection", "offline_after_model_setup"):
        if not isinstance(owner_recognition.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_owner_recognition_boolean",
                    f"`owner_recognition.{key}` must be a boolean.",
                )
            )

    minimum_samples_issue = _positive_int_issue(config, ("owner_recognition", "minimum_samples_required"))
    if minimum_samples_issue:
        issues.append(minimum_samples_issue)

    for key, minimum, maximum in (
        ("demo_threshold", 0, 2),
        ("uncertain_margin", 0, 1),
    ):
        issue = _number_range_issue("owner_recognition", key, owner_recognition.get(key), minimum, maximum)
        if issue:
            issues.append(issue)

    liveness = config.get("liveness", {})
    for key in ("enabled", "demo_only"):
        if not isinstance(liveness.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_liveness_boolean",
                    f"`liveness.{key}` must be a boolean.",
                )
            )

    if liveness.get("demo_only") is False:
        issues.append(
            ConfigValidationIssue(
                "error",
                "liveness_demo_only_required",
                "`liveness.demo_only` must remain true in Phase 8.",
            )
        )

    for item in (
        ("liveness", "challenge_duration_seconds"),
        ("liveness", "minimum_detection_frames"),
    ):
        issue = _positive_int_issue(config, item)
        if issue:
            issues.append(issue)

    movement_threshold_issue = _number_range_issue(
        "liveness",
        "movement_threshold_ratio",
        liveness.get("movement_threshold_ratio"),
        0,
        1,
    )
    if movement_threshold_issue:
        issues.append(movement_threshold_issue)
    elif float(liveness.get("movement_threshold_ratio")) <= 0:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_liveness_movement_threshold",
                "`liveness.movement_threshold_ratio` must be greater than 0 and less than or equal to 1.",
            )
        )

    liveness_camera_index = liveness.get("camera_index")
    if isinstance(liveness_camera_index, bool) or not isinstance(liveness_camera_index, int) or liveness_camera_index < 0:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_liveness_camera_index",
                "`liveness.camera_index` must be zero or a positive integer.",
            )
        )

    intruder_detection = config.get("intruder_detection", {})
    for key in ("enabled", "demo_only", "capture_unknown_only"):
        if not isinstance(intruder_detection.get(key), bool):
            issues.append(
                ConfigValidationIssue(
                    "error",
                    "invalid_intruder_detection_boolean",
                    f"`intruder_detection.{key}` must be a boolean.",
                )
            )

    if intruder_detection.get("demo_only") is False:
        issues.append(
            ConfigValidationIssue(
                "error",
                "intruder_detection_demo_only_required",
                "`intruder_detection.demo_only` must remain true in Phase 12.",
            )
        )

    if intruder_detection.get("capture_unknown_only") is False:
        issues.append(
            ConfigValidationIssue(
                "error",
                "intruder_capture_unknown_only_required",
                "`intruder_detection.capture_unknown_only` must remain true in Phase 12.",
            )
        )

    intruder_camera_index = intruder_detection.get("camera_index")
    if isinstance(intruder_camera_index, bool) or not isinstance(intruder_camera_index, int) or intruder_camera_index < 0:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_intruder_detection_camera_index",
                "`intruder_detection.camera_index` must be zero or a positive integer.",
            )
        )

    for key in ("intruder_images_dir", "manifest_path"):
        issue = _relative_path_issue("intruder_detection", key, intruder_detection.get(key))
        if issue:
            issues.append(issue)

    if intruder_detection.get("image_format") not in SUPPORTED_INTRUDER_IMAGE_FORMATS:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_intruder_detection_image_format",
                "`intruder_detection.image_format` must be jpg or png.",
            )
        )

    image_quality = intruder_detection.get("image_quality")
    if isinstance(image_quality, bool) or not isinstance(image_quality, int) or not 1 <= image_quality <= 100:
        issues.append(
            ConfigValidationIssue(
                "error",
                "invalid_intruder_detection_image_quality",
                "`intruder_detection.image_quality` must be an integer between 1 and 100.",
            )
        )

    minimum_owner_samples_issue = _positive_int_issue(config, ("intruder_detection", "minimum_owner_samples_required"))
    if minimum_owner_samples_issue:
        issues.append(minimum_owner_samples_issue)

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

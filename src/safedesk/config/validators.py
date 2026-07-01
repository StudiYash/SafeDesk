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

SUPPORTED_UI_THEMES = ("dark", "light", "system")
SUPPORTED_OWNER_SAMPLE_FORMATS = ("jpg", "png")
SUPPORTED_RECOGNITION_METRICS = ("cosine", "euclidean", "euclidean_l2")
SUPPORTED_AUTH_HASH_ALGORITHMS = ("pbkdf2_sha256",)
SUPPORTED_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")
SUPPORTED_LOG_DB_SUFFIXES = (".sqlite", ".sqlite3", ".db")


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


def _effective_flags(config: dict[str, Any], env: EnvironmentSettings) -> tuple[bool, bool, bool]:
    feature_flags = config.get("feature_flags", {})
    shutdown = config.get("shutdown", {})
    lockdown = config.get("lockdown", {})

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

    for item in (
        ("threat_levels", "max_level"),
        ("threat_levels", "forceful_attempt_threshold"),
        ("shutdown", "shutdown_after_threat_level"),
        ("shutdown", "warning_seconds"),
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

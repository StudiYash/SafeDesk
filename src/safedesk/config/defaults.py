"""Safe default configuration for SafeDesk."""

from safedesk.utils.constants import (
    DEFAULT_ENVIRONMENT,
    DEFAULT_SECURITY_MODE,
    PROJECT_NAME,
    PROJECT_VERSION,
    SUPPORTED_SECURITY_MODES,
)

DEFAULT_CONFIG = {
    "app": {
        "name": PROJECT_NAME,
        "version": PROJECT_VERSION,
        "environment": DEFAULT_ENVIRONMENT,
        "demo_safe_mode": True,
    },
    "owner_profile": {
        "owner_name": "",
        "owner_email": "",
    },
    "security_mode": {
        "default_mode": DEFAULT_SECURITY_MODE,
        "available_modes": list(SUPPORTED_SECURITY_MODES),
    },
    "feature_flags": {
        "enable_real_email": False,
        "enable_real_shutdown": False,
        "enable_real_lockdown": False,
    },
    "face_recognition": {
        "enabled": False,
        "backend": "planned",
        "liveness_check_enabled": False,
        "minimum_confidence": 0.6,
    },
    "authentication": {
        "password_fallback_enabled": False,
        "panic_code_enabled": False,
        "max_unlock_attempts": 3,
        "lockout_seconds": 30,
    },
    "otp": {
        "enabled": False,
        "delivery_method": "email",
        "code_length": 6,
        "expires_seconds": 300,
        "max_attempts": 3,
    },
    "threat_levels": {
        "enabled": False,
        "initial_level": 0,
        "max_level": 5,
        "forceful_attempt_threshold": 3,
    },
    "shutdown": {
        "real_shutdown_enabled": False,
        "demo_shutdown_only": True,
        "shutdown_after_threat_level": 5,
        "warning_seconds": 30,
    },
    "lockdown": {
        "real_lockdown_enabled": False,
        "demo_lockdown_only": True,
        "allow_recovery_exit": True,
    },
    "alarm": {
        "enabled": False,
        "volume": 0.5,
        "audio_file": "",
    },
    "logging": {
        "enabled": False,
        "database_path": "data/logs/safedesk.sqlite3",
        "log_level": "INFO",
    },
    "paths": {
        "owner_data_dir": "data/owner",
        "intruder_data_dir": "data/intruders",
        "logs_dir": "data/logs",
        "cache_dir": "data/cache",
        "config_dir": "data/config",
    },
    "privacy": {
        "store_intruder_images": False,
        "store_owner_images": False,
        "local_only_by_default": True,
        "cloud_sync_enabled": False,
    },
    "ui": {
        "theme": "dark",
        "color_theme": "blue",
        "window_width": 1100,
        "window_height": 700,
        "minimum_width": 900,
        "minimum_height": 600,
        "start_maximized": False,
    },
}

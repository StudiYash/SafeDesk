"""SafeDesk configuration package."""

from safedesk.config.config_loader import load_config
from safedesk.config.env_loader import load_environment
from safedesk.config.exceptions import (
    SafeDeskConfigError,
    SafeDeskConfigFileError,
    SafeDeskEnvironmentError,
    SafeDeskValidationError,
)
from safedesk.config.models import (
    ConfigLoadResult,
    ConfigValidationIssue,
    ConfigValidationReport,
    EnvironmentSettings,
    SafeDeskRuntimeSettings,
)
from safedesk.config.local_config_writer import LocalSetupPayload, build_safe_local_config, save_local_setup_config
from safedesk.config.setup_state import SetupStatus, get_setup_status, is_owner_profile_configured, is_setup_complete
from safedesk.config.validators import build_runtime_settings, validate_config

__all__ = [
    "ConfigLoadResult",
    "ConfigValidationIssue",
    "ConfigValidationReport",
    "EnvironmentSettings",
    "SafeDeskConfigError",
    "SafeDeskConfigFileError",
    "SafeDeskEnvironmentError",
    "SafeDeskRuntimeSettings",
    "SafeDeskValidationError",
    "LocalSetupPayload",
    "SetupStatus",
    "build_safe_local_config",
    "build_runtime_settings",
    "get_setup_status",
    "is_owner_profile_configured",
    "is_setup_complete",
    "load_config",
    "load_environment",
    "save_local_setup_config",
    "validate_config",
]

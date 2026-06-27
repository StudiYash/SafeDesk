"""Setup status helpers for SafeDesk."""

from dataclasses import dataclass
from typing import Any

from safedesk.config.models import ConfigLoadResult, EnvironmentSettings


@dataclass(frozen=True)
class SetupStatus:
    setup_completed: bool
    local_config_loaded: bool
    env_loaded: bool
    owner_name_configured: bool
    owner_email_configured: bool
    demo_safe_mode_enabled: bool
    face_registration_status: str = "pending"
    password_setup_status: str = "pending"
    otp_setup_status: str = "pending"


def is_setup_complete(config: dict[str, Any]) -> bool:
    return bool(config.get("setup", {}).get("completed", False))


def is_owner_profile_configured(config: dict[str, Any]) -> bool:
    owner_name = config.get("owner_profile", {}).get("owner_name", "")
    return isinstance(owner_name, str) and bool(owner_name.strip())


def is_owner_email_configured(config: dict[str, Any]) -> bool:
    owner_email = config.get("owner_profile", {}).get("owner_email", "")
    return isinstance(owner_email, str) and bool(owner_email.strip())


def get_setup_status(
    config: dict[str, Any],
    load_result: ConfigLoadResult,
    env: EnvironmentSettings,
) -> SetupStatus:
    security_mode = config.get("security_mode", {}).get("default_mode", "demo_safe")
    demo_safe_mode = bool(config.get("app", {}).get("demo_safe_mode", True)) or security_mode == "demo_safe"
    return SetupStatus(
        setup_completed=is_setup_complete(config),
        local_config_loaded=load_result.local_config_loaded,
        env_loaded=env.env_file_loaded,
        owner_name_configured=is_owner_profile_configured(config),
        owner_email_configured=is_owner_email_configured(config),
        demo_safe_mode_enabled=demo_safe_mode,
    )

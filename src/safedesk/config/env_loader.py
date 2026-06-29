"""Environment loading for SafeDesk."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from safedesk.config.models import EnvironmentSettings
from safedesk.storage.paths import env_path as default_env_path
from safedesk.utils.constants import (
    DEFAULT_ENVIRONMENT,
    ENV_EMAIL_APP_PASSWORD,
    ENV_EMAIL_SENDER_ADDRESS,
    ENV_ENABLE_REAL_EMAIL,
    ENV_ENABLE_REAL_LOCKDOWN,
    ENV_ENABLE_REAL_SHUTDOWN,
    ENV_OTP_RECEIVER_EMAIL,
    ENV_SAFEDESK_ENV,
    LEGACY_ENV_EMAIL_APP_PASSWORD,
    LEGACY_ENV_EMAIL_SENDER_ADDRESS,
    LEGACY_ENV_ENABLE_REAL_EMAIL,
    LEGACY_ENV_OTP_RECEIVER_EMAIL,
)

TRUE_VALUES = {"1", "true", "yes", "y", "on"}
FALSE_VALUES = {"0", "false", "no", "n", "off", ""}


def parse_bool(value: str | bool | None, default: bool = False) -> bool:
    """Parse common boolean environment values."""

    if isinstance(value, bool):
        return value
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return default


def _load_dotenv_if_available(path: Path) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv(path, override=False)


def first_env_value(source: Mapping[str, str], *keys: str) -> str:
    """Return the first non-empty value for supported environment aliases."""

    for key in keys:
        value = source.get(key, "")
        if value.strip():
            return value.strip()
    return ""


def load_environment(
    env_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> EnvironmentSettings:
    """Load sanitized SafeDesk environment settings.

    Missing `.env` files are allowed. Secret values are reduced to presence
    flags so startup checks never print or return the secret itself.
    """

    path = env_file or default_env_path()
    env_file_loaded = path.exists()

    if environ is None and env_file_loaded:
        _load_dotenv_if_available(path)

    source = environ if environ is not None else os.environ
    app_password = first_env_value(source, ENV_EMAIL_APP_PASSWORD, LEGACY_ENV_EMAIL_APP_PASSWORD)

    return EnvironmentSettings(
        safedesk_env=source.get(ENV_SAFEDESK_ENV, DEFAULT_ENVIRONMENT).strip() or DEFAULT_ENVIRONMENT,
        email_sender_address=first_env_value(source, ENV_EMAIL_SENDER_ADDRESS, LEGACY_ENV_EMAIL_SENDER_ADDRESS),
        email_app_password_present=bool(app_password.strip()),
        otp_receiver_email=first_env_value(source, ENV_OTP_RECEIVER_EMAIL, LEGACY_ENV_OTP_RECEIVER_EMAIL),
        enable_real_email=parse_bool(
            first_env_value(source, ENV_ENABLE_REAL_EMAIL, LEGACY_ENV_ENABLE_REAL_EMAIL),
            default=False,
        ),
        enable_real_shutdown=parse_bool(source.get(ENV_ENABLE_REAL_SHUTDOWN), default=False),
        enable_real_lockdown=parse_bool(source.get(ENV_ENABLE_REAL_LOCKDOWN), default=False),
        env_file_loaded=env_file_loaded,
        env_file_path=path if env_file_loaded else None,
    )

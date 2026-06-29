"""Alerts package public exports."""

from safedesk.alerts.email_sender import (
    EmailCredentials,
    EmailSender,
    EmailSendResult,
    EmailSettingsStatus,
    build_email_credentials_from_env,
    build_email_settings_status,
)

__all__ = [
    "EmailCredentials",
    "EmailSender",
    "EmailSendResult",
    "EmailSettingsStatus",
    "build_email_credentials_from_env",
    "build_email_settings_status",
]

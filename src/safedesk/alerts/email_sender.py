"""SafeDesk email sender foundation for manual OTP/email testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from email.message import EmailMessage
import os
import smtplib
import ssl
from typing import Callable, Mapping

from safedesk.config.env_loader import first_env_value
from safedesk.config.models import EnvironmentSettings, SafeDeskRuntimeSettings
from safedesk.utils.constants import (
    ENV_EMAIL_APP_PASSWORD,
    ENV_EMAIL_SENDER_ADDRESS,
    ENV_OTP_RECEIVER_EMAIL,
    LEGACY_ENV_EMAIL_APP_PASSWORD,
    LEGACY_ENV_EMAIL_SENDER_ADDRESS,
    LEGACY_ENV_OTP_RECEIVER_EMAIL,
)


@dataclass(frozen=True, repr=False)
class EmailCredentials:
    """Real email credentials kept out of repr and GUI output."""

    sender_address: str
    app_password: str = field(repr=False)
    receiver_email: str

    @property
    def app_password_present(self) -> bool:
        return bool(self.app_password)


@dataclass(frozen=True)
class EmailSendResult:
    success: bool
    status: str
    message: str


@dataclass(frozen=True)
class EmailSettingsStatus:
    real_email_enabled: bool
    sender_configured: bool
    app_password_present: bool
    receiver_configured: bool
    smtp_host: str
    smtp_port: int
    message: str


def build_email_credentials_from_env(
    env: EnvironmentSettings,
    environ: Mapping[str, str] | None = None,
) -> EmailCredentials:
    """Build credentials from the active environment without exposing the password."""

    source = environ if environ is not None else os.environ
    return EmailCredentials(
        sender_address=first_env_value(source, ENV_EMAIL_SENDER_ADDRESS, LEGACY_ENV_EMAIL_SENDER_ADDRESS)
        or env.email_sender_address,
        app_password=first_env_value(source, ENV_EMAIL_APP_PASSWORD, LEGACY_ENV_EMAIL_APP_PASSWORD),
        receiver_email=first_env_value(source, ENV_OTP_RECEIVER_EMAIL, LEGACY_ENV_OTP_RECEIVER_EMAIL)
        or env.otp_receiver_email,
    )


def build_email_settings_status(
    env: EnvironmentSettings,
    config: dict,
    settings: SafeDeskRuntimeSettings,
    environ: Mapping[str, str] | None = None,
) -> EmailSettingsStatus:
    """Return a safe email readiness summary."""

    credentials = build_email_credentials_from_env(env, environ=environ)
    email_config = config.get("email", {})
    smtp_host = str(email_config.get("smtp_host", "smtp.gmail.com"))
    smtp_port = int(email_config.get("smtp_port", 587))
    ready = (
        settings.real_email_enabled
        and bool(credentials.sender_address)
        and credentials.app_password_present
        and bool(credentials.receiver_email)
    )
    if ready:
        message = "Real email is configured for manual testing."
    elif not settings.real_email_enabled:
        message = "Real email is disabled."
    else:
        message = "Real email is enabled but required credentials are missing."

    return EmailSettingsStatus(
        real_email_enabled=settings.real_email_enabled,
        sender_configured=bool(credentials.sender_address),
        app_password_present=credentials.app_password_present or env.email_app_password_present,
        receiver_configured=bool(credentials.receiver_email),
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        message=message,
    )


class EmailSender:
    """Small SMTP sender used only by explicit manual actions."""

    def __init__(
        self,
        config: dict,
        env: EnvironmentSettings,
        settings: SafeDeskRuntimeSettings,
        environ: Mapping[str, str] | None = None,
        smtp_factory: Callable[..., object] | None = None,
    ):
        self.config = config
        self.email_config = config.get("email", {})
        self.env = env
        self.settings = settings
        self.credentials = build_email_credentials_from_env(env, environ=environ)
        self.smtp_factory = smtp_factory or smtplib.SMTP

    def send_test_email(self) -> EmailSendResult:
        return self._send_message(
            subject="SafeDesk Test Email",
            body=(
                "This is a SafeDesk manual test email. "
                "No unlock, alert escalation, lockdown, or shutdown action was triggered."
            ),
        )

    def send_otp_email(self, otp_code: str, expires_seconds: int) -> EmailSendResult:
        if not isinstance(otp_code, str) or not otp_code:
            return EmailSendResult(False, "invalid_input", "OTP code is required before sending email.")
        return self._send_message(
            subject="SafeDesk OTP Code",
            body=(
                "SafeDesk manual OTP foundation test.\n\n"
                f"Your OTP code is: {otp_code}\n"
                f"This code expires in {expires_seconds} seconds.\n\n"
                "This does not unlock SafeDesk or start protected mode."
            ),
        )

    def _send_message(self, subject: str, body: str) -> EmailSendResult:
        readiness = self._readiness_result()
        if readiness is not None:
            return readiness

        message = EmailMessage()
        display_name = str(self.email_config.get("sender_display_name", "SafeDesk")).strip() or "SafeDesk"
        message["From"] = f"{display_name} <{self.credentials.sender_address}>"
        message["To"] = self.credentials.receiver_email
        message["Subject"] = subject
        message.set_content(body)

        smtp_host = str(self.email_config.get("smtp_host", "smtp.gmail.com"))
        smtp_port = int(self.email_config.get("smtp_port", 587))
        timeout = int(self.email_config.get("timeout_seconds", 15))
        use_tls = bool(self.email_config.get("use_tls", True))

        try:
            with self.smtp_factory(smtp_host, smtp_port, timeout=timeout) as server:
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                server.login(self.credentials.sender_address, self.credentials.app_password)
                server.send_message(message)
        except Exception:
            return EmailSendResult(False, "send_failed", "Email could not be sent safely. Review local SMTP settings.")

        return EmailSendResult(True, "sent", "Email sent for manual foundation testing.")

    def _readiness_result(self) -> EmailSendResult | None:
        if not self.settings.real_email_enabled:
            return EmailSendResult(False, "disabled", "Real email is disabled. Enable it only in a private local environment.")
        if not self.credentials.sender_address:
            return EmailSendResult(False, "missing_sender", "Email sender address is missing.")
        if not self.credentials.app_password:
            return EmailSendResult(False, "missing_secret", "Email app password is missing.")
        if not self.credentials.receiver_email:
            return EmailSendResult(False, "missing_receiver", "OTP receiver email is missing.")
        return None

"""In-memory OTP generation and verification foundation."""

from __future__ import annotations

from dataclasses import dataclass
import math
import secrets
import time
from typing import Callable


@dataclass(frozen=True)
class OtpConfig:
    """Runtime OTP settings for the manual foundation screen."""

    code_length: int = 6
    expires_seconds: int = 120
    max_attempts: int = 3
    resend_limit: int = 2
    resend_cooldown_seconds: int = 30

    @classmethod
    def from_config(cls, config: dict) -> "OtpConfig":
        otp = config.get("otp", config)
        return cls(
            code_length=int(otp.get("code_length", 6)),
            expires_seconds=int(otp.get("expires_seconds", 120)),
            max_attempts=int(otp.get("max_attempts", 3)),
            resend_limit=int(otp.get("resend_limit", 2)),
            resend_cooldown_seconds=int(otp.get("resend_cooldown_seconds", 30)),
        )


@dataclass
class OtpSession:
    """Current in-memory OTP state."""

    code: str = ""
    created_at: float = 0.0
    attempts_used: int = 0
    sends_used: int = 0
    last_sent_at: float = 0.0
    verified: bool = False

    @property
    def generated(self) -> bool:
        return bool(self.code)


@dataclass(frozen=True)
class OtpGenerationResult:
    success: bool
    status: str
    message: str
    code: str = ""
    expires_seconds: int = 0


@dataclass(frozen=True)
class OtpVerificationResult:
    success: bool
    status: str
    message: str
    attempts_used: int = 0
    attempts_remaining: int = 0


@dataclass(frozen=True)
class OtpSendEligibilityResult:
    allowed: bool
    status: str
    message: str
    sends_used: int = 0
    sends_remaining: int = 0
    cooldown_seconds_remaining: int = 0


@dataclass(frozen=True)
class OtpSessionStatus:
    generated: bool
    expired: bool
    verified: bool
    attempts_used: int
    max_attempts: int
    sends_used: int
    resend_limit: int
    cooldown_seconds_remaining: int
    expires_seconds_remaining: int


class OtpManager:
    """Manage one in-memory OTP session for manual testing."""

    def __init__(self, config: OtpConfig | dict | None = None, time_provider: Callable[[], float] | None = None):
        if isinstance(config, OtpConfig):
            self.config = config
        else:
            self.config = OtpConfig.from_config(config or {})
        self.time_provider = time_provider or time.time
        self.session = OtpSession()

    def generate_otp(self) -> OtpGenerationResult:
        code = "".join(secrets.choice("0123456789") for _ in range(self.config.code_length))
        self.session = OtpSession(code=code, created_at=self.time_provider())
        return OtpGenerationResult(
            success=True,
            status="generated",
            message="OTP generated for local foundation testing.",
            code=code,
            expires_seconds=self.config.expires_seconds,
        )

    def verify_otp(self, code: str) -> OtpVerificationResult:
        if not self.session.generated:
            return self._verification_result(False, "not_generated", "Generate an OTP before verification.")
        if self._is_expired(self.time_provider()):
            return self._verification_result(False, "expired", "OTP has expired. Generate a new OTP.")
        if self.session.attempts_used >= self.config.max_attempts:
            return self._verification_result(False, "attempts_exceeded", "OTP attempt limit has been reached.")

        normalized = code.strip() if isinstance(code, str) else ""
        if not normalized or not normalized.isdigit():
            return self._verification_result(False, "invalid_input", "Enter a numeric OTP code.")

        if secrets.compare_digest(normalized, self.session.code):
            self.session.verified = True
            return self._verification_result(True, "success", "OTP verified for manual foundation testing.")

        self.session.attempts_used += 1
        if self.session.attempts_used >= self.config.max_attempts:
            return self._verification_result(False, "attempts_exceeded", "OTP attempt limit has been reached.")
        return self._verification_result(False, "failed", "OTP did not match.")

    def can_send_otp(self) -> OtpSendEligibilityResult:
        now = self.time_provider()
        if not self.session.generated:
            return self._send_result(False, "not_generated", "Generate an OTP before sending email.", now)
        if self._is_expired(now):
            return self._send_result(False, "expired", "OTP has expired. Generate a new OTP before sending.", now)
        if self.session.sends_used >= self.config.resend_limit:
            return self._send_result(False, "resend_limit_reached", "OTP send limit has been reached.", now)

        cooldown = self._cooldown_remaining(now)
        if cooldown > 0:
            return self._send_result(
                False,
                "resend_cooldown_active",
                "Wait before resending this OTP.",
                now,
                cooldown,
            )
        return self._send_result(True, "allowed", "OTP email can be sent.", now)

    def record_send(self) -> OtpSendEligibilityResult:
        eligibility = self.can_send_otp()
        if not eligibility.allowed:
            return eligibility
        self.session.sends_used += 1
        self.session.last_sent_at = self.time_provider()
        return self._send_result(True, "allowed", "OTP send recorded.", self.time_provider())

    def reset_session(self) -> None:
        self.session = OtpSession()

    def session_status(self) -> OtpSessionStatus:
        now = self.time_provider()
        return OtpSessionStatus(
            generated=self.session.generated,
            expired=self._is_expired(now),
            verified=self.session.verified,
            attempts_used=self.session.attempts_used,
            max_attempts=self.config.max_attempts,
            sends_used=self.session.sends_used,
            resend_limit=self.config.resend_limit,
            cooldown_seconds_remaining=self._cooldown_remaining(now),
            expires_seconds_remaining=self._expires_remaining(now),
        )

    def _is_expired(self, now: float) -> bool:
        if not self.session.generated:
            return False
        return now >= self.session.created_at + self.config.expires_seconds

    def _expires_remaining(self, now: float) -> int:
        if not self.session.generated or self._is_expired(now):
            return 0
        return max(0, math.ceil(self.session.created_at + self.config.expires_seconds - now))

    def _cooldown_remaining(self, now: float) -> int:
        if not self.session.last_sent_at or self.config.resend_cooldown_seconds <= 0:
            return 0
        elapsed = now - self.session.last_sent_at
        remaining = self.config.resend_cooldown_seconds - elapsed
        return max(0, math.ceil(remaining))

    def _verification_result(self, success: bool, status: str, message: str) -> OtpVerificationResult:
        return OtpVerificationResult(
            success=success,
            status=status,
            message=message,
            attempts_used=self.session.attempts_used,
            attempts_remaining=max(0, self.config.max_attempts - self.session.attempts_used),
        )

    def _send_result(
        self,
        allowed: bool,
        status: str,
        message: str,
        now: float,
        cooldown: int | None = None,
    ) -> OtpSendEligibilityResult:
        return OtpSendEligibilityResult(
            allowed=allowed,
            status=status,
            message=message,
            sends_used=self.session.sends_used,
            sends_remaining=max(0, self.config.resend_limit - self.session.sends_used),
            cooldown_seconds_remaining=self._cooldown_remaining(now) if cooldown is None else cooldown,
        )

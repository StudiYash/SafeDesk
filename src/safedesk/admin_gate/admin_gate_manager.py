"""Owner/Admin Console gate manager."""

from __future__ import annotations

import math
from pathlib import Path
import time
from typing import Callable

from safedesk.admin_gate.admin_gate_models import AdminGateAttemptResult, AdminGateStatus
from safedesk.auth.authentication_service import AuthenticationService
from safedesk.auth.local_secret_store import resolve_secrets_path
from safedesk.auth.password_hashing import verify_secret


class AdminGateManager:
    """Local, in-memory gate for opening the Owner/Admin Console."""

    def __init__(
        self,
        config: dict,
        secrets_path: Path | None = None,
        time_provider: Callable[[], float] | None = None,
    ):
        self.config = config
        self.gate_config = config.get("admin_gate", {})
        self.time_provider = time_provider or time.time
        self.auth_service = AuthenticationService(config, secrets_path=secrets_path or resolve_secrets_path(config))
        self.failed_attempts = 0
        self.locked_until = 0.0

    @property
    def enabled(self) -> bool:
        return self.gate_config.get("enabled", True) is True

    @property
    def foundation_enabled(self) -> bool:
        return self.gate_config.get("foundation_enabled", True) is True

    @property
    def demo_only(self) -> bool:
        return self.gate_config.get("demo_only", True) is True

    @property
    def require_password_if_configured(self) -> bool:
        return self.gate_config.get("require_password_if_configured", True) is True

    @property
    def development_continue_allowed(self) -> bool:
        return self.gate_config.get("allow_development_continue_if_unconfigured", True) is True

    @property
    def max_attempts(self) -> int:
        return int(self.gate_config.get("max_attempts", 3))

    @property
    def lockout_seconds(self) -> int:
        return int(self.gate_config.get("lockout_seconds", 30))

    def build_status(self) -> AdminGateStatus:
        """Build safe display status without exposing secret storage details."""

        current_time = self.time_provider()
        auth_status = self.auth_service.build_status()
        locked_out = self._is_locked(current_time)

        if not self.enabled:
            message = "Owner/Admin Gate is disabled in local configuration."
        elif not self.foundation_enabled:
            message = "Owner/Admin Gate foundation is disabled in local configuration."
        elif not auth_status.store_readable:
            message = "Owner/Admin credential status could not be read safely."
        elif auth_status.master_password_configured:
            message = "Owner password is configured. Verification is required."
        elif self.development_continue_allowed:
            message = "Owner password setup is required before normal admin access."
        else:
            message = "Owner password setup is required and development continuation is disabled."

        return AdminGateStatus(
            enabled=self.enabled,
            foundation_enabled=self.foundation_enabled,
            demo_only=self.demo_only,
            password_configured=auth_status.master_password_configured and auth_status.store_readable,
            setup_required=auth_status.store_readable and not auth_status.master_password_configured,
            locked_out=locked_out,
            remaining_attempts=self._remaining_attempts(),
            lockout_remaining_seconds=self._lockout_remaining_seconds(current_time),
            development_continue_allowed=self.development_continue_allowed,
            message=message,
        )

    def verify_password(self, password: str) -> AdminGateAttemptResult:
        """Verify the configured owner password without storing or logging input."""

        status = self.build_status()
        if not status.enabled or not status.foundation_enabled:
            return self._result(False, "error_safe", "Owner/Admin Gate is unavailable.")
        if status.locked_out:
            return self._result(
                False,
                "locked_out",
                "Owner/Admin Gate is temporarily locked after repeated failed attempts.",
            )
        if status.setup_required:
            return self._result(False, "setup_required", "Owner password setup is required before verification.")
        if not status.password_configured:
            return self._result(False, "error_safe", "Owner/Admin credential status is unavailable.")
        if not isinstance(password, str) or not password:
            return self._record_failure("Password verification failed.")

        data = self.auth_service.store.load()
        if data.load_error or data.master_password is None:
            return self._result(False, "error_safe", "Owner/Admin credential status could not be read safely.")

        verification = verify_secret(password, data.master_password.record)
        if verification.success:
            self._reset_attempts()
            return self._result(True, "success", "Owner verification succeeded.")

        return self._record_failure("Owner verification failed.")

    def development_continue(self) -> AdminGateAttemptResult:
        """Allow setup-only continuation when no owner password is configured."""

        status = self.build_status()
        if status.setup_required and status.development_continue_allowed:
            return self._result(
                True,
                "development_continue_allowed",
                "Continue to owner password setup.",
            )
        if status.setup_required:
            return self._result(
                False,
                "development_continue_blocked",
                "Development continuation is disabled until owner password setup is complete.",
            )
        return self._result(False, "password_required", "Owner password verification is required.")

    def reset_password_with_recovery_code(
        self,
        recovery_code: str,
        new_password: str,
        confirm_password: str,
    ) -> AdminGateAttemptResult:
        """Reset owner password with a valid recovery code without opening Admin Console."""

        status = self.build_status()
        if not status.password_configured:
            return self._result(False, "setup_required", "Owner password setup is required before recovery reset.")
        if not status.enabled or not status.foundation_enabled:
            return self._result(False, "error_safe", "Owner/Admin Gate is unavailable.")

        result = self.auth_service.reset_master_password_with_recovery_code(
            recovery_code,
            new_password,
            confirm_password,
        )
        if result.success:
            self._reset_attempts()
            return self._result(True, "recovery_reset_success", result.message)
        return self._result(False, "recovery_reset_failed", result.message)

    def _record_failure(self, message: str) -> AdminGateAttemptResult:
        current_time = self.time_provider()
        self.failed_attempts += 1
        if self.failed_attempts >= self.max_attempts and self.lockout_seconds > 0:
            self.locked_until = current_time + self.lockout_seconds
            return self._result(
                False,
                "locked_out",
                "Owner/Admin Gate is temporarily locked after repeated failed attempts.",
            )
        return self._result(False, "failed", message)

    def _result(self, success: bool, status: str, message: str) -> AdminGateAttemptResult:
        current_time = self.time_provider()
        return AdminGateAttemptResult(
            success=success,
            status=status,
            message=message,
            remaining_attempts=self._remaining_attempts(),
            lockout_remaining_seconds=self._lockout_remaining_seconds(current_time),
        )

    def _is_locked(self, current_time: float) -> bool:
        if current_time >= self.locked_until:
            if self.locked_until:
                self._reset_attempts()
            return False
        return True

    def _remaining_attempts(self) -> int:
        return max(0, self.max_attempts - self.failed_attempts)

    def _lockout_remaining_seconds(self, current_time: float) -> int:
        if current_time >= self.locked_until:
            return 0
        return max(1, math.ceil(self.locked_until - current_time))

    def _reset_attempts(self) -> None:
        self.failed_attempts = 0
        self.locked_until = 0.0

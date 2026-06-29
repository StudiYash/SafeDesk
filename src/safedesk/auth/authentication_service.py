"""Safe local password and panic-code authentication foundation."""

from __future__ import annotations

from dataclasses import dataclass
import math
import time
from pathlib import Path
from typing import Callable

from safedesk.auth.local_secret_store import (
    AuthenticationSecretStatus,
    AuthenticationSecretStoreData,
    LocalSecretStore,
    StoredSecretRecord,
    resolve_secrets_path,
    utc_timestamp,
)
from safedesk.auth.password_hashing import hash_secret, verify_secret


@dataclass(frozen=True)
class AuthenticationStatus:
    """Safe status for the authentication foundation."""

    foundation_enabled: bool
    demo_only: bool
    store_present: bool
    store_readable: bool
    master_password_configured: bool
    panic_code_configured: bool
    message: str


@dataclass(frozen=True)
class AuthenticationSetupResult:
    """Result of saving a local authentication hash record."""

    success: bool
    status: str
    message: str


@dataclass(frozen=True)
class AuthenticationVerificationResult:
    """Safe manual verification result."""

    success: bool
    status: str
    message: str
    remaining_attempts: int
    cooldown_seconds_remaining: int = 0


@dataclass
class AttemptCounterState:
    """In-memory attempt counter used only by the Phase 9 foundation."""

    failed_attempts: int = 0
    locked_until: float = 0.0

    def is_locked(self, current_time: float) -> bool:
        return current_time < self.locked_until

    def remaining_seconds(self, current_time: float) -> int:
        if not self.is_locked(current_time):
            return 0
        return max(1, math.ceil(self.locked_until - current_time))

    def reset(self) -> None:
        self.failed_attempts = 0
        self.locked_until = 0.0

    def record_failure(self, current_time: float, max_attempts: int, lockout_seconds: int) -> None:
        self.failed_attempts += 1
        if self.failed_attempts >= max_attempts:
            self.locked_until = current_time + lockout_seconds


class AuthenticationService:
    """Manual setup and verification service for local hashed secrets."""

    def __init__(
        self,
        config: dict,
        secrets_path: Path | None = None,
        time_provider: Callable[[], float] | None = None,
    ):
        self.config = config
        self.auth_config = config.get("authentication", config)
        self.secrets_path = secrets_path or resolve_secrets_path(config)
        self.store = LocalSecretStore(self.secrets_path)
        self.time_provider = time_provider or time.time
        self.password_attempts = AttemptCounterState()
        self.panic_attempts = AttemptCounterState()

    @property
    def foundation_enabled(self) -> bool:
        return self.auth_config.get("auth_foundation_enabled", True) is True

    @property
    def demo_only(self) -> bool:
        return self.auth_config.get("demo_only", True) is True

    @property
    def max_attempts(self) -> int:
        return int(self.auth_config.get("max_unlock_attempts", 3))

    @property
    def lockout_seconds(self) -> int:
        return int(self.auth_config.get("lockout_seconds", 30))

    @property
    def iterations(self) -> int:
        return int(self.auth_config.get("pbkdf2_iterations", 390000))

    def build_status(self) -> AuthenticationStatus:
        secret_status = self.store.status()
        return AuthenticationStatus(
            foundation_enabled=self.foundation_enabled,
            demo_only=self.demo_only,
            store_present=secret_status.store_present,
            store_readable=secret_status.readable,
            master_password_configured=secret_status.master_password_configured,
            panic_code_configured=secret_status.panic_code_configured,
            message=secret_status.message,
        )

    def set_master_password(self, password: str, confirm_password: str) -> AuthenticationSetupResult:
        if not self.foundation_enabled:
            return AuthenticationSetupResult(False, "disabled", "Authentication foundation is disabled in configuration.")

        validation_message = self._validate_secret_pair(
            password,
            confirm_password,
            int(self.auth_config.get("minimum_password_length", 8)),
            "Master password",
        )
        if validation_message:
            return AuthenticationSetupResult(False, "invalid_input", validation_message)

        data = self.store.load()
        if data.load_error:
            return AuthenticationSetupResult(False, "storage_error", data.load_error)

        if data.panic_code and verify_secret(password, data.panic_code.record).success:
            return AuthenticationSetupResult(False, "invalid_input", "Master password must be different from the panic code.")

        timestamp = utc_timestamp()
        created_at = data.master_password.created_at if data.master_password else timestamp
        stored = StoredSecretRecord(
            record=hash_secret(password, self.iterations),
            created_at=created_at,
            updated_at=timestamp,
        )
        self.store.save(
            AuthenticationSecretStoreData(
                master_password=stored,
                panic_code=data.panic_code,
                store_present=True,
            )
        )
        self.password_attempts.reset()
        return AuthenticationSetupResult(True, "saved", "Master password hash saved locally.")

    def set_panic_code(self, panic_code: str, confirm_panic_code: str) -> AuthenticationSetupResult:
        if not self.foundation_enabled:
            return AuthenticationSetupResult(False, "disabled", "Authentication foundation is disabled in configuration.")

        validation_message = self._validate_secret_pair(
            panic_code,
            confirm_panic_code,
            int(self.auth_config.get("minimum_panic_code_length", 6)),
            "Panic code",
        )
        if validation_message:
            return AuthenticationSetupResult(False, "invalid_input", validation_message)

        data = self.store.load()
        if data.load_error:
            return AuthenticationSetupResult(False, "storage_error", data.load_error)

        if data.master_password and verify_secret(panic_code, data.master_password.record).success:
            return AuthenticationSetupResult(False, "invalid_input", "Panic code must be different from the master password.")

        timestamp = utc_timestamp()
        created_at = data.panic_code.created_at if data.panic_code else timestamp
        stored = StoredSecretRecord(
            record=hash_secret(panic_code, self.iterations),
            created_at=created_at,
            updated_at=timestamp,
        )
        self.store.save(
            AuthenticationSecretStoreData(
                master_password=data.master_password,
                panic_code=stored,
                store_present=True,
            )
        )
        self.panic_attempts.reset()
        return AuthenticationSetupResult(True, "saved", "Panic/recovery code hash saved locally.")

    def verify_master_password(self, password: str) -> AuthenticationVerificationResult:
        data = self.store.load()
        if data.load_error:
            return self._verification_result(False, "storage_error", data.load_error, self.password_attempts)
        if data.master_password is None:
            return self._verification_result(
                False,
                "not_configured",
                "Master password is not configured.",
                self.password_attempts,
            )
        return self._verify_secret_with_attempts(password, data.master_password, self.password_attempts, "Master password verified.")

    def verify_panic_code(self, panic_code: str) -> AuthenticationVerificationResult:
        data = self.store.load()
        if data.load_error:
            return self._verification_result(False, "storage_error", data.load_error, self.panic_attempts)
        if data.panic_code is None:
            return self._verification_result(
                False,
                "not_configured",
                "Panic/recovery code is not configured.",
                self.panic_attempts,
            )
        return self._verify_secret_with_attempts(
            panic_code,
            data.panic_code,
            self.panic_attempts,
            "Panic/recovery code verified. No emergency action is connected in this phase.",
        )

    def reset_attempts(self) -> None:
        self.password_attempts.reset()
        self.panic_attempts.reset()

    def _verify_secret_with_attempts(
        self,
        secret_value: str,
        stored: StoredSecretRecord,
        attempts: AttemptCounterState,
        success_message: str,
    ) -> AuthenticationVerificationResult:
        if not self.foundation_enabled:
            return self._verification_result(False, "disabled", "Authentication foundation is disabled in configuration.", attempts)
        if not isinstance(secret_value, str) or not secret_value:
            return self._verification_result(False, "invalid_input", "Secret input is required.", attempts)

        current_time = self.time_provider()
        if attempts.is_locked(current_time):
            return self._verification_result(
                False,
                "locked_out",
                "Manual verification is temporarily locked after repeated failed attempts.",
                attempts,
            )

        verification = verify_secret(secret_value, stored.record)
        if verification.success:
            attempts.reset()
            return self._verification_result(True, "success", success_message, attempts)

        attempts.record_failure(current_time, self.max_attempts, self.lockout_seconds)
        if attempts.is_locked(current_time):
            return self._verification_result(
                False,
                "locked_out",
                "Manual verification is temporarily locked after repeated failed attempts.",
                attempts,
            )
        return self._verification_result(False, "failed", "Secret did not match.", attempts)

    def _verification_result(
        self,
        success: bool,
        status: str,
        message: str,
        attempts: AttemptCounterState,
    ) -> AuthenticationVerificationResult:
        current_time = self.time_provider()
        remaining_attempts = max(0, self.max_attempts - attempts.failed_attempts)
        return AuthenticationVerificationResult(
            success=success,
            status=status,
            message=message,
            remaining_attempts=remaining_attempts,
            cooldown_seconds_remaining=attempts.remaining_seconds(current_time),
        )

    @staticmethod
    def _validate_secret_pair(secret_value: str, confirmation: str, minimum_length: int, label: str) -> str:
        if not isinstance(secret_value, str) or not secret_value:
            return f"{label} is required."
        if len(secret_value) < minimum_length:
            return f"{label} must be at least {minimum_length} characters long."
        if secret_value != confirmation:
            return f"{label} confirmation does not match."
        return ""

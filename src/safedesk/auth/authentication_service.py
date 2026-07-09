"""Safe local password and panic-code authentication foundation."""

from __future__ import annotations

from dataclasses import dataclass
import math
import secrets
import string
import time
from pathlib import Path
from typing import Callable

from safedesk.auth.local_secret_store import (
    AuthenticationSecretStatus,
    AuthenticationSecretStoreData,
    LocalSecretStore,
    StoredRecoveryCodeRecord,
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
    recovery_codes_configured: bool
    recovery_code_count: int
    unused_recovery_code_count: int
    used_recovery_code_count: int
    recovery_foundation_enabled: bool
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


@dataclass(frozen=True)
class RecoveryCodeGenerationResult:
    """Result of generating one-time owner recovery codes."""

    success: bool
    status: str
    message: str
    codes: tuple[str, ...] = ()


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
        self.recovery_config = config.get("recovery_codes", {})

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

    @property
    def recovery_foundation_enabled(self) -> bool:
        return self.recovery_config.get("enabled", True) is True and self.recovery_config.get("foundation_enabled", True) is True

    @property
    def recovery_code_count(self) -> int:
        return int(self.recovery_config.get("code_count", 5))

    @property
    def recovery_code_length(self) -> int:
        return int(self.recovery_config.get("code_length", 16))

    @property
    def recovery_special_characters(self) -> str:
        return str(self.recovery_config.get("allowed_special_characters", "!@#$%^&*()-_=+[]{}?"))

    def build_status(self) -> AuthenticationStatus:
        secret_status = self.store.status()
        return AuthenticationStatus(
            foundation_enabled=self.foundation_enabled,
            demo_only=self.demo_only,
            store_present=secret_status.store_present,
            store_readable=secret_status.readable,
            master_password_configured=secret_status.master_password_configured,
            panic_code_configured=secret_status.panic_code_configured,
            recovery_codes_configured=secret_status.recovery_codes_configured,
            recovery_code_count=secret_status.recovery_code_count,
            unused_recovery_code_count=secret_status.unused_recovery_code_count,
            used_recovery_code_count=secret_status.used_recovery_code_count,
            recovery_foundation_enabled=self.recovery_foundation_enabled,
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
                recovery_codes=data.recovery_codes,
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
                recovery_codes=data.recovery_codes,
                store_present=True,
            )
        )
        self.panic_attempts.reset()
        return AuthenticationSetupResult(True, "saved", "Panic code hash saved locally.")

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
                "Panic code is not configured.",
                self.panic_attempts,
            )
        return self._verify_secret_with_attempts(
            panic_code,
            data.panic_code,
            self.panic_attempts,
            "Panic code verified. No emergency action is connected in this phase.",
        )

    def reset_attempts(self) -> None:
        self.password_attempts.reset()
        self.panic_attempts.reset()

    def generate_recovery_codes(self) -> RecoveryCodeGenerationResult:
        """Generate one-time recovery codes and store only their hashes."""

        if not self.recovery_foundation_enabled:
            return RecoveryCodeGenerationResult(False, "disabled", "Recovery code foundation is disabled.")

        data = self.store.load()
        if data.load_error:
            return RecoveryCodeGenerationResult(False, "storage_error", data.load_error)
        if data.master_password is None:
            return RecoveryCodeGenerationResult(
                False,
                "master_password_required",
                "Set an owner password before generating recovery codes.",
            )

        timestamp = utc_timestamp()
        codes_set: set[str] = set()
        while len(codes_set) < self.recovery_code_count:
            codes_set.add(self._generate_recovery_code())
        codes = tuple(codes_set)
        records = tuple(
            StoredRecoveryCodeRecord(
                code_id=secrets.token_hex(4),
                record=hash_secret(code, self.iterations),
                created_at=timestamp,
                used=False,
            )
            for code in codes
        )
        self.store.save(
            AuthenticationSecretStoreData(
                master_password=data.master_password,
                panic_code=data.panic_code,
                recovery_codes=records,
                store_present=True,
            )
        )
        return RecoveryCodeGenerationResult(
            True,
            "generated",
            "Recovery codes generated. These codes will not be shown again.",
            codes,
        )

    def reset_master_password_with_recovery_code(
        self,
        recovery_code: str,
        new_password: str,
        confirm_password: str,
    ) -> AuthenticationSetupResult:
        """Reset the master password using a valid unused recovery code."""

        if not self.recovery_foundation_enabled:
            return AuthenticationSetupResult(False, "disabled", "Recovery code foundation is disabled.")

        validation_message = self._validate_secret_pair(
            new_password,
            confirm_password,
            int(self.auth_config.get("minimum_password_length", 8)),
            "New owner password",
        )
        if validation_message:
            return AuthenticationSetupResult(False, "invalid_input", validation_message)

        data = self.store.load()
        if data.load_error:
            return AuthenticationSetupResult(False, "storage_error", data.load_error)
        if data.master_password is None:
            return AuthenticationSetupResult(False, "not_configured", "Master password is not configured.")
        if not data.recovery_codes:
            return AuthenticationSetupResult(False, "not_configured", "No recovery codes are configured.")
        if not isinstance(recovery_code, str) or not recovery_code:
            return AuthenticationSetupResult(False, "invalid_recovery_code", "Recovery code could not be verified.")
        if data.panic_code and verify_secret(new_password, data.panic_code.record).success:
            return AuthenticationSetupResult(False, "invalid_input", "New owner password must be different from the panic code.")

        matched_index: int | None = None
        matched_used = False
        for index, stored_code in enumerate(data.recovery_codes):
            verification = verify_secret(recovery_code, stored_code.record)
            if verification.success:
                matched_index = index
                matched_used = stored_code.used
                break

        if matched_index is None:
            return AuthenticationSetupResult(False, "invalid_recovery_code", "Recovery code could not be verified.")
        if matched_used:
            return AuthenticationSetupResult(False, "used_recovery_code", "Recovery code could not be verified.")

        timestamp = utc_timestamp()
        master_created_at = data.master_password.created_at
        new_master = StoredSecretRecord(
            record=hash_secret(new_password, self.iterations),
            created_at=master_created_at,
            updated_at=timestamp,
        )
        recovery_codes = list(data.recovery_codes)
        matched_record = recovery_codes[matched_index]
        recovery_codes[matched_index] = StoredRecoveryCodeRecord(
            code_id=matched_record.code_id,
            record=matched_record.record,
            created_at=matched_record.created_at,
            used_at=timestamp,
            used=True,
        )
        self.store.save(
            AuthenticationSecretStoreData(
                master_password=new_master,
                panic_code=data.panic_code,
                recovery_codes=tuple(recovery_codes),
                store_present=True,
            )
        )
        self.password_attempts.reset()
        return AuthenticationSetupResult(True, "reset", "Owner password reset. Unlock the Admin Console with your new password.")

    def _generate_recovery_code(self) -> str:
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special = self.recovery_special_characters
        alphabet = uppercase + lowercase + digits + special
        required = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(special),
        ]
        remaining = [secrets.choice(alphabet) for _ in range(max(0, self.recovery_code_length - len(required)))]
        characters = required + remaining
        secrets.SystemRandom().shuffle(characters)
        return "".join(characters)[: self.recovery_code_length]

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

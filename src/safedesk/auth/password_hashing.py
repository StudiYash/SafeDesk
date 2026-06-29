"""Standard-library password and recovery-code hashing helpers."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import secrets

HASH_ALGORITHM = "pbkdf2_sha256"
_PBKDF2_DIGEST = "sha256"
_SALT_BYTES = 16


@dataclass(frozen=True, repr=False)
class PasswordHashRecord:
    """Safe stored PBKDF2 hash metadata without raw secret values."""

    algorithm: str
    iterations: int
    salt: str
    hash: str

    def __repr__(self) -> str:
        return f"PasswordHashRecord(algorithm={self.algorithm!r}, iterations={self.iterations!r})"


@dataclass(frozen=True)
class PasswordHashResult:
    """Result wrapper for callers that prefer status-style handling."""

    success: bool
    message: str
    record: PasswordHashRecord | None = None


@dataclass(frozen=True)
class PasswordVerificationResult:
    """Safe verification result."""

    success: bool
    message: str


def _derive_hash(secret_value: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac(_PBKDF2_DIGEST, secret_value.encode("utf-8"), salt, iterations)


def hash_secret(secret_value: str, iterations: int) -> PasswordHashRecord:
    """Return a salted PBKDF2 hash record for a non-empty secret."""

    if not isinstance(secret_value, str) or not secret_value:
        raise ValueError("Secret value must be non-empty.")
    if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations <= 0:
        raise ValueError("PBKDF2 iterations must be a positive integer.")

    salt = secrets.token_bytes(_SALT_BYTES)
    secret_hash = _derive_hash(secret_value, salt, iterations)
    return PasswordHashRecord(
        algorithm=HASH_ALGORITHM,
        iterations=iterations,
        salt=salt.hex(),
        hash=secret_hash.hex(),
    )


def verify_secret(secret_value: str, record: PasswordHashRecord) -> PasswordVerificationResult:
    """Verify a provided secret against a stored hash record."""

    if not isinstance(secret_value, str) or not secret_value:
        return PasswordVerificationResult(False, "Secret value is required.")
    if record.algorithm != HASH_ALGORITHM:
        return PasswordVerificationResult(False, "Unsupported secret hash algorithm.")

    try:
        salt = bytes.fromhex(record.salt)
        expected_hash = bytes.fromhex(record.hash)
        candidate_hash = _derive_hash(secret_value, salt, record.iterations)
    except Exception:
        return PasswordVerificationResult(False, "Stored secret record could not be verified.")

    verified = hmac.compare_digest(candidate_hash, expected_hash)
    return PasswordVerificationResult(verified, "Secret verified." if verified else "Secret did not match.")


def password_record_from_dict(data: dict) -> PasswordHashRecord:
    """Build a hash record from JSON-safe data."""

    algorithm = data.get("algorithm")
    iterations = data.get("iterations")
    salt = data.get("salt")
    secret_hash = data.get("hash")

    if algorithm != HASH_ALGORITHM:
        raise ValueError("Unsupported secret hash algorithm.")
    if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations <= 0:
        raise ValueError("Invalid PBKDF2 iteration count.")
    if not isinstance(salt, str) or not salt:
        raise ValueError("Invalid secret salt.")
    if not isinstance(secret_hash, str) or not secret_hash:
        raise ValueError("Invalid secret hash.")

    bytes.fromhex(salt)
    bytes.fromhex(secret_hash)
    return PasswordHashRecord(algorithm=algorithm, iterations=iterations, salt=salt, hash=secret_hash)


def password_record_to_dict(record: PasswordHashRecord) -> dict:
    """Convert a hash record to a JSON-safe dictionary."""

    return {
        "algorithm": record.algorithm,
        "iterations": record.iterations,
        "salt": record.salt,
        "hash": record.hash,
    }

"""Authentication package public exports."""

from safedesk.auth.authentication_service import (
    AttemptCounterState,
    AuthenticationService,
    AuthenticationSetupResult,
    AuthenticationStatus,
    AuthenticationVerificationResult,
)
from safedesk.auth.local_secret_store import (
    AuthenticationSecretStatus,
    AuthenticationSecretStoreData,
    LocalSecretStore,
    LocalSecretStoreResult,
    StoredSecretRecord,
    build_authentication_secret_status,
    load_authentication_secrets,
    resolve_secrets_path,
    save_authentication_secrets,
)
from safedesk.auth.password_hashing import (
    HASH_ALGORITHM,
    PasswordHashRecord,
    PasswordHashResult,
    PasswordVerificationResult,
    hash_secret,
    password_record_from_dict,
    password_record_to_dict,
    verify_secret,
)

__all__ = [
    "AttemptCounterState",
    "AuthenticationSecretStatus",
    "AuthenticationSecretStoreData",
    "AuthenticationService",
    "AuthenticationSetupResult",
    "AuthenticationStatus",
    "AuthenticationVerificationResult",
    "HASH_ALGORITHM",
    "LocalSecretStore",
    "LocalSecretStoreResult",
    "PasswordHashRecord",
    "PasswordHashResult",
    "PasswordVerificationResult",
    "StoredSecretRecord",
    "build_authentication_secret_status",
    "hash_secret",
    "load_authentication_secrets",
    "password_record_from_dict",
    "password_record_to_dict",
    "resolve_secrets_path",
    "save_authentication_secrets",
    "verify_secret",
]

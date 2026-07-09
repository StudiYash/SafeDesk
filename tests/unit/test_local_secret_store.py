from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.auth.local_secret_store import (
    AuthenticationSecretStoreData,
    StoredRecoveryCodeRecord,
    StoredSecretRecord,
    build_authentication_secret_status,
    load_authentication_secrets,
    save_authentication_secrets,
)
from safedesk.auth.password_hashing import hash_secret


def _stored_record(secret: str) -> StoredSecretRecord:
    return StoredSecretRecord(
        record=hash_secret(secret, iterations=1000),
        created_at="2026-06-29T00:00:00+00:00",
        updated_at="2026-06-29T00:00:00+00:00",
    )


def _recovery_record(secret: str, code_id: str = "code-1", used: bool = False) -> StoredRecoveryCodeRecord:
    return StoredRecoveryCodeRecord(
        code_id=code_id,
        record=hash_secret(secret, iterations=1000),
        created_at="2026-06-29T00:00:00+00:00",
        used_at="2026-06-30T00:00:00+00:00" if used else "",
        used=used,
    )


def test_missing_secret_store_returns_not_configured(tmp_path):
    path = tmp_path / "secrets.local.json"

    data = load_authentication_secrets(path)
    status = build_authentication_secret_status(path)

    assert data.store_present is False
    assert status.store_present is False
    assert status.master_password_configured is False
    assert status.panic_code_configured is False
    assert status.recovery_codes_configured is False


def test_save_authentication_secrets_writes_hash_records_only(tmp_path):
    path = tmp_path / "secrets.local.json"

    save_authentication_secrets(
        path,
        AuthenticationSecretStoreData(
            master_password=_stored_record("master-secret"),
            panic_code=_stored_record("panic-secret"),
            recovery_codes=(_recovery_record("recovery-secret"),),
            store_present=True,
        ),
    )

    raw = path.read_text(encoding="utf-8")
    payload = json.loads(raw)
    assert "master-secret" not in raw
    assert "panic-secret" not in raw
    assert "recovery-secret" not in raw
    assert payload["authentication"]["master_password"]["algorithm"] == "pbkdf2_sha256"
    assert payload["authentication"]["panic_code"]["algorithm"] == "pbkdf2_sha256"
    assert payload["authentication"]["recovery_codes"][0]["record"]["algorithm"] == "pbkdf2_sha256"


def test_load_authentication_secrets_reads_saved_records(tmp_path):
    path = tmp_path / "secrets.local.json"
    save_authentication_secrets(path, AuthenticationSecretStoreData(master_password=_stored_record("secret"), store_present=True))

    data = load_authentication_secrets(path)
    status = build_authentication_secret_status(path)

    assert data.store_present is True
    assert data.master_password is not None
    assert status.readable is True
    assert status.master_password_configured is True


def test_recovery_code_counts_load_from_store(tmp_path):
    path = tmp_path / "secrets.local.json"
    save_authentication_secrets(
        path,
        AuthenticationSecretStoreData(
            recovery_codes=(
                _recovery_record("unused-secret", "code-1", used=False),
                _recovery_record("used-secret", "code-2", used=True),
            ),
            store_present=True,
        ),
    )

    data = load_authentication_secrets(path)
    status = build_authentication_secret_status(path)

    assert len(data.recovery_codes) == 2
    assert status.recovery_codes_configured is True
    assert status.recovery_code_count == 2
    assert status.unused_recovery_code_count == 1
    assert status.used_recovery_code_count == 1


def test_corrupted_secret_store_returns_safe_error(tmp_path):
    path = tmp_path / "secrets.local.json"
    path.write_text("{not valid json", encoding="utf-8")

    data = load_authentication_secrets(path)
    status = build_authentication_secret_status(path)

    assert data.store_present is True
    assert data.load_error
    assert status.readable is False
    assert "could not be read" in status.message

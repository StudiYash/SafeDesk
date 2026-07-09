from pathlib import Path
import json
import string
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.auth.authentication_service import AuthenticationService
from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG


SPECIALS = "!@#$%^&*()-_=+[]{}?"


def _config(overrides=None):
    return deep_merge(
        DEFAULT_CONFIG,
        {
            "authentication": {
                "pbkdf2_iterations": 1000,
                "minimum_password_length": 8,
                "minimum_panic_code_length": 6,
            },
            "recovery_codes": {
                "code_count": 5,
                "code_length": 16,
                "allowed_special_characters": SPECIALS,
            },
        }
        | (overrides or {}),
    )


def _service(tmp_path):
    return AuthenticationService(_config(), secrets_path=tmp_path / "secrets.local.json")


def test_generate_recovery_codes_returns_expected_one_time_plaintext_and_hashes_only(tmp_path):
    service = _service(tmp_path)
    assert service.set_master_password("owner-pass", "owner-pass").success is True

    result = service.generate_recovery_codes()

    assert result.success is True
    assert len(result.codes) == 5
    assert len(set(result.codes)) == 5
    for code in result.codes:
        assert len(code) == 16
        assert any(character in string.ascii_uppercase for character in code)
        assert any(character in string.ascii_lowercase for character in code)
        assert any(character in string.digits for character in code)
        assert any(character in SPECIALS for character in code)

    raw = (tmp_path / "secrets.local.json").read_text(encoding="utf-8")
    for code in result.codes:
        assert code not in raw
    payload = json.loads(raw)
    stored_codes = payload["authentication"]["recovery_codes"]
    assert len(stored_codes) == 5
    assert all("record" in stored for stored in stored_codes)
    assert all(stored["used"] is False for stored in stored_codes)


def test_generate_recovery_codes_requires_master_password_and_does_not_create_store(tmp_path):
    service = _service(tmp_path)

    result = service.generate_recovery_codes()

    assert result.success is False
    assert result.status == "master_password_required"
    assert result.codes == ()
    assert not (tmp_path / "secrets.local.json").exists()


def test_status_reports_recovery_code_counts(tmp_path):
    service = _service(tmp_path)
    service.set_master_password("owner-pass", "owner-pass")
    service.generate_recovery_codes()

    status = service.build_status()

    assert status.recovery_codes_configured is True
    assert status.recovery_code_count == 5
    assert status.unused_recovery_code_count == 5
    assert status.used_recovery_code_count == 0


def test_valid_recovery_code_resets_master_password_and_is_single_use(tmp_path):
    service = _service(tmp_path)
    assert service.set_master_password("old-owner-pass", "old-owner-pass").success is True
    [recovery_code, *_] = service.generate_recovery_codes().codes

    reset = service.reset_master_password_with_recovery_code(recovery_code, "new-owner-pass", "new-owner-pass")
    old_result = service.verify_master_password("old-owner-pass")
    new_result = service.verify_master_password("new-owner-pass")
    reuse = service.reset_master_password_with_recovery_code(recovery_code, "another-pass", "another-pass")
    status = service.build_status()

    assert reset.success is True
    assert old_result.success is False
    assert new_result.success is True
    assert reuse.success is False
    assert reuse.status == "used_recovery_code"
    assert status.unused_recovery_code_count == 4
    assert status.used_recovery_code_count == 1


def test_invalid_recovery_code_fails_safely(tmp_path):
    service = _service(tmp_path)
    service.set_master_password("old-owner-pass", "old-owner-pass")
    service.generate_recovery_codes()

    result = service.reset_master_password_with_recovery_code("not-a-real-code", "new-owner-pass", "new-owner-pass")

    assert result.success is False
    assert result.status == "invalid_recovery_code"


def test_password_mismatch_does_not_consume_recovery_code(tmp_path):
    service = _service(tmp_path)
    service.set_master_password("old-owner-pass", "old-owner-pass")
    [recovery_code, *_] = service.generate_recovery_codes().codes

    result = service.reset_master_password_with_recovery_code(recovery_code, "new-owner-pass", "different-pass")
    status = service.build_status()
    later = service.reset_master_password_with_recovery_code(recovery_code, "new-owner-pass", "new-owner-pass")

    assert result.success is False
    assert result.status == "invalid_input"
    assert status.unused_recovery_code_count == 5
    assert later.success is True


def test_short_new_password_does_not_consume_recovery_code(tmp_path):
    service = _service(tmp_path)
    service.set_master_password("old-owner-pass", "old-owner-pass")
    [recovery_code, *_] = service.generate_recovery_codes().codes

    result = service.reset_master_password_with_recovery_code(recovery_code, "short", "short")
    status = service.build_status()

    assert result.success is False
    assert result.status == "invalid_input"
    assert status.unused_recovery_code_count == 5


def test_panic_code_cannot_be_used_as_recovery_code(tmp_path):
    service = _service(tmp_path)
    service.set_master_password("old-owner-pass", "old-owner-pass")
    service.set_panic_code("panic-123", "panic-123")
    service.generate_recovery_codes()

    result = service.reset_master_password_with_recovery_code("panic-123", "new-owner-pass", "new-owner-pass")

    assert result.success is False
    assert result.status == "invalid_recovery_code"

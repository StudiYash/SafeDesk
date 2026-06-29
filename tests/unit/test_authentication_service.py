from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.auth.authentication_service import AuthenticationService
from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG


class FakeClock:
    def __init__(self, current_time: float = 100.0):
        self.current_time = current_time

    def __call__(self) -> float:
        return self.current_time

    def advance(self, seconds: float) -> None:
        self.current_time += seconds


def _config(overrides=None):
    return deep_merge(
        DEFAULT_CONFIG,
        {
            "authentication": {
                "pbkdf2_iterations": 1000,
                "minimum_password_length": 8,
                "minimum_panic_code_length": 6,
                "max_unlock_attempts": 2,
                "lockout_seconds": 5,
            }
        }
        | (overrides or {}),
    )


def test_service_rejects_short_password(tmp_path):
    service = AuthenticationService(_config(), secrets_path=tmp_path / "secrets.local.json")

    result = service.set_master_password("short", "short")

    assert result.success is False
    assert result.status == "invalid_input"


def test_service_rejects_mismatched_confirmation(tmp_path):
    service = AuthenticationService(_config(), secrets_path=tmp_path / "secrets.local.json")

    result = service.set_master_password("long-enough", "different")

    assert result.success is False
    assert result.status == "invalid_input"


def test_service_saves_and_verifies_master_password(tmp_path):
    service = AuthenticationService(_config(), secrets_path=tmp_path / "secrets.local.json")

    setup = service.set_master_password("long-enough", "long-enough")
    verification = service.verify_master_password("long-enough")
    wrong = service.verify_master_password("wrong-password")

    assert setup.success is True
    assert verification.success is True
    assert wrong.success is False
    assert wrong.status == "failed"


def test_service_saves_and_verifies_panic_code(tmp_path):
    service = AuthenticationService(_config(), secrets_path=tmp_path / "secrets.local.json")

    setup = service.set_panic_code("panic-123", "panic-123")
    verification = service.verify_panic_code("panic-123")

    assert setup.success is True
    assert verification.success is True
    assert "No emergency action" in verification.message


def test_panic_code_cannot_match_existing_master_password(tmp_path):
    service = AuthenticationService(_config(), secrets_path=tmp_path / "secrets.local.json")
    service.set_master_password("same-secret", "same-secret")

    result = service.set_panic_code("same-secret", "same-secret")

    assert result.success is False
    assert result.status == "invalid_input"


def test_attempt_counter_locks_and_cools_down(tmp_path):
    clock = FakeClock()
    service = AuthenticationService(_config(), secrets_path=tmp_path / "secrets.local.json", time_provider=clock)
    service.set_master_password("long-enough", "long-enough")

    first = service.verify_master_password("wrong-one")
    second = service.verify_master_password("wrong-two")
    locked = service.verify_master_password("long-enough")
    clock.advance(6)
    unlocked = service.verify_master_password("long-enough")

    assert first.status == "failed"
    assert second.status == "locked_out"
    assert locked.status == "locked_out"
    assert unlocked.success is True


def test_service_reports_not_configured_when_store_missing(tmp_path):
    service = AuthenticationService(_config(), secrets_path=tmp_path / "secrets.local.json")

    result = service.verify_master_password("anything")

    assert result.success is False
    assert result.status == "not_configured"

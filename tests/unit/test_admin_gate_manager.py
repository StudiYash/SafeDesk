from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.admin_gate import AdminGateManager
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
            },
            "admin_gate": {
                "max_attempts": 2,
                "lockout_seconds": 5,
            },
        }
        | (overrides or {}),
    )


def _set_password(config, secrets_path, password="owner-pass"):
    service = AuthenticationService(config, secrets_path=secrets_path)
    result = service.set_master_password(password, password)
    assert result.success is True


def test_no_password_returns_setup_required_and_continue_allowed(tmp_path):
    manager = AdminGateManager(_config(), secrets_path=tmp_path / "secrets.local.json")

    status = manager.build_status()
    result = manager.development_continue()

    assert status.password_configured is False
    assert status.setup_required is True
    assert status.development_continue_allowed is True
    assert result.success is True
    assert result.status == "development_continue_allowed"


def test_no_password_continue_can_be_blocked_by_config(tmp_path):
    config = _config({"admin_gate": {"allow_development_continue_if_unconfigured": False}})
    manager = AdminGateManager(config, secrets_path=tmp_path / "secrets.local.json")

    status = manager.build_status()
    result = manager.development_continue()

    assert status.setup_required is True
    assert status.development_continue_allowed is False
    assert result.success is False
    assert result.status == "development_continue_blocked"


def test_correct_password_succeeds(tmp_path):
    config = _config()
    secrets_path = tmp_path / "secrets.local.json"
    _set_password(config, secrets_path)
    manager = AdminGateManager(config, secrets_path=secrets_path)

    result = manager.verify_password("owner-pass")

    assert result.success is True
    assert result.status == "success"


def test_incorrect_password_fails_safely(tmp_path):
    config = _config()
    secrets_path = tmp_path / "secrets.local.json"
    _set_password(config, secrets_path)
    manager = AdminGateManager(config, secrets_path=secrets_path)

    result = manager.verify_password("wrong-pass")

    assert result.success is False
    assert result.status == "failed"
    assert result.remaining_attempts == 1


def test_failed_attempts_lock_temporarily_and_cool_down(tmp_path):
    clock = FakeClock()
    config = _config()
    secrets_path = tmp_path / "secrets.local.json"
    _set_password(config, secrets_path)
    manager = AdminGateManager(config, secrets_path=secrets_path, time_provider=clock)

    first = manager.verify_password("wrong-one")
    second = manager.verify_password("wrong-two")
    locked = manager.verify_password("owner-pass")
    clock.advance(6)
    unlocked = manager.verify_password("owner-pass")

    assert first.status == "failed"
    assert second.status == "locked_out"
    assert locked.status == "locked_out"
    assert unlocked.success is True


def test_panic_code_does_not_unlock_admin_console(tmp_path):
    config = _config()
    secrets_path = tmp_path / "secrets.local.json"
    service = AuthenticationService(config, secrets_path=secrets_path)
    assert service.set_master_password("owner-pass", "owner-pass").success is True
    assert service.set_panic_code("panic-123", "panic-123").success is True
    manager = AdminGateManager(config, secrets_path=secrets_path)

    result = manager.verify_password("panic-123")

    assert result.success is False
    assert result.status == "failed"


def test_manager_does_not_keep_typed_password_after_failure(tmp_path):
    config = _config()
    secrets_path = tmp_path / "secrets.local.json"
    _set_password(config, secrets_path)
    manager = AdminGateManager(config, secrets_path=secrets_path)

    manager.verify_password("sensitive-input")

    assert "sensitive-input" not in str(manager.__dict__)


def test_recovery_reset_with_valid_code_succeeds_and_clears_lockout(tmp_path):
    clock = FakeClock()
    config = _config()
    secrets_path = tmp_path / "secrets.local.json"
    service = AuthenticationService(config, secrets_path=secrets_path)
    assert service.set_master_password("owner-pass", "owner-pass").success is True
    [recovery_code, *_] = service.generate_recovery_codes().codes
    manager = AdminGateManager(config, secrets_path=secrets_path, time_provider=clock)
    manager.verify_password("wrong-one")
    manager.verify_password("wrong-two")

    result = manager.reset_password_with_recovery_code(recovery_code, "new-owner-pass", "new-owner-pass")
    status = manager.build_status()

    assert result.success is True
    assert result.status == "recovery_reset_success"
    assert status.locked_out is False
    assert status.remaining_attempts == 2
    assert manager.verify_password("new-owner-pass").success is True


def test_recovery_reset_failure_does_not_unlock_admin_console(tmp_path):
    config = _config()
    secrets_path = tmp_path / "secrets.local.json"
    service = AuthenticationService(config, secrets_path=secrets_path)
    assert service.set_master_password("owner-pass", "owner-pass").success is True
    service.generate_recovery_codes()
    manager = AdminGateManager(config, secrets_path=secrets_path)

    result = manager.reset_password_with_recovery_code("not-a-code", "new-owner-pass", "new-owner-pass")

    assert result.success is False
    assert result.status == "recovery_reset_failed"

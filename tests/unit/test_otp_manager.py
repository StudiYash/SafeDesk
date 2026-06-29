from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.auth.otp_manager import OtpConfig, OtpManager


class FakeClock:
    def __init__(self, current_time: float = 100.0):
        self.current_time = current_time

    def __call__(self) -> float:
        return self.current_time

    def advance(self, seconds: float) -> None:
        self.current_time += seconds


def _manager(clock=None):
    return OtpManager(
        OtpConfig(
            code_length=6,
            expires_seconds=10,
            max_attempts=2,
            resend_limit=2,
            resend_cooldown_seconds=5,
        ),
        time_provider=clock or FakeClock(),
    )


def test_generate_otp_has_expected_length_and_digits():
    manager = _manager()

    result = manager.generate_otp()

    assert result.success is True
    assert len(result.code) == 6
    assert result.code.isdigit()


def test_correct_otp_verifies_successfully():
    manager = _manager()
    code = manager.generate_otp().code

    result = manager.verify_otp(code)

    assert result.success is True
    assert result.status == "success"


def test_wrong_otp_fails_and_increments_attempts():
    manager = _manager()
    code = manager.generate_otp().code
    wrong_code = "000000" if code != "000000" else "111111"

    result = manager.verify_otp(wrong_code)

    assert result.success is False
    assert result.status == "failed"
    assert result.attempts_used == 1


def test_expired_otp_is_rejected():
    clock = FakeClock()
    manager = _manager(clock)
    code = manager.generate_otp().code
    clock.advance(11)

    result = manager.verify_otp(code)

    assert result.success is False
    assert result.status == "expired"


def test_max_attempts_are_enforced():
    manager = _manager()
    code = manager.generate_otp().code
    wrong_one = "000000" if code != "000000" else "111111"
    wrong_two = "222222" if code != "222222" else "333333"

    first = manager.verify_otp(wrong_one)
    second = manager.verify_otp(wrong_two)
    third = manager.verify_otp(code)

    assert first.status == "failed"
    assert second.status == "attempts_exceeded"
    assert third.status == "attempts_exceeded"


def test_send_requires_generated_otp():
    manager = _manager()

    result = manager.can_send_otp()

    assert result.allowed is False
    assert result.status == "not_generated"


def test_resend_limit_and_cooldown_are_enforced():
    clock = FakeClock()
    manager = _manager(clock)
    manager.generate_otp()

    first = manager.record_send()
    cooldown = manager.can_send_otp()
    clock.advance(6)
    second = manager.record_send()
    limit = manager.can_send_otp()

    assert first.allowed is True
    assert cooldown.status == "resend_cooldown_active"
    assert second.allowed is True
    assert limit.status == "resend_limit_reached"


def test_reset_session_clears_otp_state():
    manager = _manager()
    manager.generate_otp()
    manager.reset_session()

    status = manager.session_status()

    assert status.generated is False
    assert status.attempts_used == 0
    assert status.sends_used == 0

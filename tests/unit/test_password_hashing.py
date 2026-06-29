from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.auth.password_hashing import (
    HASH_ALGORITHM,
    hash_secret,
    password_record_from_dict,
    password_record_to_dict,
    verify_secret,
)


def test_hash_secret_does_not_store_raw_secret():
    record = hash_secret("correct horse battery staple", iterations=1000)
    data = password_record_to_dict(record)
    serialized = str(data)

    assert data["algorithm"] == HASH_ALGORITHM
    assert data["iterations"] == 1000
    assert "correct horse battery staple" not in serialized
    assert "salt" in data
    assert "hash" in data


def test_verify_secret_succeeds_for_correct_secret():
    record = hash_secret("safe-password", iterations=1000)

    result = verify_secret("safe-password", record)

    assert result.success is True


def test_verify_secret_fails_for_wrong_secret():
    record = hash_secret("safe-password", iterations=1000)

    result = verify_secret("wrong-password", record)

    assert result.success is False


def test_record_round_trip_from_dict():
    record = hash_secret("safe-password", iterations=1000)
    restored = password_record_from_dict(password_record_to_dict(record))

    assert restored.algorithm == HASH_ALGORITHM
    assert verify_secret("safe-password", restored).success is True

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.vision.liveness_challenge import (
    challenge_instruction,
    create_liveness_challenge,
    describe_challenge,
    is_supported_challenge,
)


def test_supported_liveness_challenges():
    assert is_supported_challenge("move_left") is True
    assert is_supported_challenge("move_right") is True
    assert is_supported_challenge("move_any") is True
    assert is_supported_challenge("blink") is False


def test_default_liveness_challenge_is_move_any():
    challenge = create_liveness_challenge()

    assert challenge.direction == "move_any"
    assert "move your head" in challenge_instruction(challenge).lower()


def test_invalid_liveness_challenge_rejected():
    with pytest.raises(ValueError):
        create_liveness_challenge("unsupported")


def test_liveness_description_is_demo_language():
    challenge = create_liveness_challenge("move_left")

    assert "Basic movement challenge" in describe_challenge(challenge)

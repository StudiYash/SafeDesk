"""Basic liveness movement challenge models."""

from __future__ import annotations

from dataclasses import dataclass

SUPPORTED_LIVENESS_CHALLENGES = ("move_left", "move_right", "move_any")
DEFAULT_LIVENESS_CHALLENGE = "move_any"


@dataclass(frozen=True)
class LivenessChallenge:
    """A demo-only movement challenge."""

    direction: str


@dataclass(frozen=True)
class LivenessChallengeStatus:
    """High-level challenge status text for UI surfaces."""

    active: bool
    instruction: str
    message: str


@dataclass(frozen=True)
class LivenessChallengeResult:
    """Final demo challenge result."""

    passed: bool
    status: str
    message: str


def is_supported_challenge(direction: str) -> bool:
    """Return True when a movement challenge is supported."""

    return direction in SUPPORTED_LIVENESS_CHALLENGES


def create_liveness_challenge(direction: str | None = None) -> LivenessChallenge:
    """Create a deterministic movement challenge."""

    selected = direction or DEFAULT_LIVENESS_CHALLENGE
    if not is_supported_challenge(selected):
        raise ValueError(f"Unsupported liveness challenge: {selected}")
    return LivenessChallenge(direction=selected)


def describe_challenge(challenge: LivenessChallenge) -> str:
    """Describe the movement challenge without overstating security."""

    descriptions = {
        "move_left": "Basic movement challenge: move your head left.",
        "move_right": "Basic movement challenge: move your head right.",
        "move_any": "Basic movement challenge: move your head slightly left or right.",
    }
    return descriptions[challenge.direction]


def challenge_instruction(challenge: LivenessChallenge) -> str:
    """Return a concise user instruction."""

    instructions = {
        "move_left": "Move your head left until the movement is detected.",
        "move_right": "Move your head right until the movement is detected.",
        "move_any": "Move your head slightly left or right until movement is detected.",
    }
    return instructions[challenge.direction]

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.vision.liveness_challenge import create_liveness_challenge
from safedesk.vision.liveness_detector import (
    FaceBox,
    LivenessDetectionState,
    calculate_center,
    is_movement_sufficient,
    select_single_face,
    update_liveness_state,
)


class DummyFrame:
    shape = (480, 640, 3)


CONFIG = {
    "challenge_duration_seconds": 8,
    "movement_threshold_ratio": 0.08,
    "minimum_detection_frames": 2,
}


def test_face_center_calculation():
    assert calculate_center(FaceBox(10, 20, 100, 80)) == (60, 60)


def test_select_single_face_requires_exactly_one_face():
    face = FaceBox(0, 0, 20, 20)

    assert select_single_face([face]) == face
    assert select_single_face([]) is None
    assert select_single_face([face, face]) is None


def test_liveness_movement_direction_helpers():
    baseline = (320, 200)

    assert is_movement_sufficient(baseline, (250, 200), 640, 0.08, "move_left") is True
    assert is_movement_sufficient(baseline, (390, 200), 640, 0.08, "move_right") is True
    assert is_movement_sufficient(baseline, (321, 200), 640, 0.08, "move_any") is False


def test_missing_face_returns_waiting_state():
    result = update_liveness_state(
        DummyFrame(),
        LivenessDetectionState(),
        create_liveness_challenge(),
        CONFIG,
        face_boxes=[],
        current_time=0,
    )

    assert result.status == "waiting_for_face"
    assert result.state.completed is False


def test_multiple_faces_do_not_count_movement():
    result = update_liveness_state(
        DummyFrame(),
        LivenessDetectionState(),
        create_liveness_challenge(),
        CONFIG,
        face_boxes=[FaceBox(0, 0, 20, 20), FaceBox(50, 0, 20, 20)],
        current_time=0,
    )

    assert result.status == "multiple_faces"
    assert result.state.successful_detection_frames == 0


def test_baseline_then_movement_can_pass():
    challenge = create_liveness_challenge("move_right")
    first = update_liveness_state(
        DummyFrame(),
        LivenessDetectionState(),
        challenge,
        CONFIG,
        face_boxes=[FaceBox(270, 180, 100, 100)],
        current_time=0,
    )

    assert first.status == "baseline_captured"

    second = update_liveness_state(
        DummyFrame(),
        first.state,
        challenge,
        CONFIG,
        face_boxes=[FaceBox(340, 180, 100, 100)],
        current_time=1,
    )
    third = update_liveness_state(
        DummyFrame(),
        second.state,
        challenge,
        CONFIG,
        face_boxes=[FaceBox(345, 180, 100, 100)],
        current_time=2,
    )

    assert third.status == "passed"
    assert third.passed is True


def test_liveness_timeout():
    state = LivenessDetectionState(started_at=0)

    result = update_liveness_state(
        DummyFrame(),
        state,
        create_liveness_challenge(),
        {"challenge_duration_seconds": 1, "movement_threshold_ratio": 0.08, "minimum_detection_frames": 2},
        face_boxes=[FaceBox(270, 180, 100, 100)],
        current_time=2,
    )

    assert result.status == "timeout"
    assert result.timed_out is True

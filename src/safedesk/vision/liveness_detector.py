"""OpenCV-based basic liveness movement detector foundation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from time import monotonic
from typing import Any

from safedesk.vision.liveness_challenge import LivenessChallenge


@dataclass(frozen=True)
class FaceBox:
    """Face bounding box in frame coordinates."""

    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class LivenessFrameObservation:
    """Observed face state for one frame."""

    face_count: int
    face_box: FaceBox | None = None
    center: tuple[float, float] | None = None


@dataclass(frozen=True)
class LivenessDetectionState:
    """Mutable-by-replacement liveness challenge state."""

    started_at: float | None = None
    baseline_center: tuple[float, float] | None = None
    successful_detection_frames: int = 0
    completed: bool = False
    passed: bool = False
    last_message: str = "Liveness check has not run yet."


@dataclass(frozen=True)
class LivenessDetectionResult:
    """Result of processing a frame for demo liveness."""

    success: bool
    status: str
    message: str
    state: LivenessDetectionState
    observation: LivenessFrameObservation | None = None
    passed: bool = False
    timed_out: bool = False
    detector_available: bool = True


def _load_face_cascade():
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is not installed, so the liveness detector is unavailable.") from exc

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    if cascade.empty():
        raise RuntimeError("OpenCV face cascade could not be loaded for the liveness detector.")
    return cv2, cascade


def detect_face_boxes(frame: Any) -> list[FaceBox]:
    """Detect face boxes using OpenCV Haar cascade loaded on demand."""

    cv2, cascade = _load_face_cascade()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    return [FaceBox(int(x), int(y), int(width), int(height)) for x, y, width, height in faces]


def select_single_face(face_boxes: list[FaceBox]) -> FaceBox | None:
    """Return a single detected face only when exactly one face is present."""

    if len(face_boxes) != 1:
        return None
    return face_boxes[0]


def calculate_center(face_box: FaceBox) -> tuple[float, float]:
    """Calculate the center of a face box."""

    return (face_box.x + face_box.width / 2, face_box.y + face_box.height / 2)


def is_movement_sufficient(
    baseline_center: tuple[float, float],
    current_center: tuple[float, float],
    frame_width: int,
    movement_threshold_ratio: float,
    direction: str,
) -> bool:
    """Return True when movement is sufficient for the challenge direction."""

    threshold_pixels = frame_width * movement_threshold_ratio
    delta_x = current_center[0] - baseline_center[0]
    delta_y = current_center[1] - baseline_center[1]

    if direction == "move_left":
        return delta_x <= -threshold_pixels
    if direction == "move_right":
        return delta_x >= threshold_pixels
    return abs(delta_x) >= threshold_pixels or abs(delta_y) >= threshold_pixels


def _frame_width(frame: Any, fallback: int = 640) -> int:
    shape = getattr(frame, "shape", None)
    if shape is not None and len(shape) >= 2:
        return int(shape[1])
    return fallback


def update_liveness_state(
    frame: Any,
    state: LivenessDetectionState,
    challenge: LivenessChallenge,
    config: dict[str, Any],
    face_boxes: list[FaceBox] | None = None,
    current_time: float | None = None,
) -> LivenessDetectionResult:
    """Update liveness state using one frame.

    This is a basic movement challenge foundation, not final anti-spoofing.
    """

    now = monotonic() if current_time is None else current_time
    started_at = state.started_at if state.started_at is not None else now
    working_state = state if state.started_at is not None else replace(state, started_at=started_at, last_message="Waiting for face.")

    duration = int(config.get("challenge_duration_seconds", 8))
    if now - started_at > duration:
        timeout_state = replace(working_state, completed=True, passed=False, last_message="Liveness challenge timed out.")
        return LivenessDetectionResult(
            False,
            "timeout",
            "Liveness challenge timed out.",
            timeout_state,
            timed_out=True,
        )

    try:
        boxes = face_boxes if face_boxes is not None else detect_face_boxes(frame)
    except RuntimeError as exc:
        unavailable_state = replace(working_state, completed=True, passed=False, last_message=str(exc))
        return LivenessDetectionResult(
            False,
            "detector_unavailable",
            str(exc),
            unavailable_state,
            detector_available=False,
        )

    observation = LivenessFrameObservation(face_count=len(boxes))
    if not boxes:
        no_face_state = replace(working_state, last_message="Waiting for a single face.")
        return LivenessDetectionResult(False, "waiting_for_face", "Waiting for a single face.", no_face_state, observation)

    face_box = select_single_face(boxes)
    if face_box is None:
        multiple_state = replace(working_state, last_message="Multiple faces detected. Use one face for this demo.")
        return LivenessDetectionResult(False, "multiple_faces", multiple_state.last_message, multiple_state, observation)

    center = calculate_center(face_box)
    observation = LivenessFrameObservation(face_count=1, face_box=face_box, center=center)
    if working_state.baseline_center is None:
        baseline_state = replace(working_state, baseline_center=center, last_message="Baseline face position captured.")
        return LivenessDetectionResult(True, "baseline_captured", baseline_state.last_message, baseline_state, observation)

    movement_detected = is_movement_sufficient(
        working_state.baseline_center,
        center,
        _frame_width(frame),
        float(config.get("movement_threshold_ratio", 0.08)),
        challenge.direction,
    )
    if not movement_detected:
        waiting_state = replace(working_state, last_message="Challenge running. Movement not detected yet.")
        return LivenessDetectionResult(True, "challenge_running", waiting_state.last_message, waiting_state, observation)

    successful_frames = working_state.successful_detection_frames + 1
    minimum_frames = int(config.get("minimum_detection_frames", 3))
    if successful_frames >= minimum_frames:
        passed_state = replace(
            working_state,
            successful_detection_frames=successful_frames,
            completed=True,
            passed=True,
            last_message="Basic movement challenge passed.",
        )
        return LivenessDetectionResult(True, "passed", passed_state.last_message, passed_state, observation, passed=True)

    progress_state = replace(
        working_state,
        successful_detection_frames=successful_frames,
        last_message=f"Movement detected. Progress: {successful_frames} / {minimum_frames}.",
    )
    return LivenessDetectionResult(True, "movement_detected", progress_state.last_message, progress_state, observation)

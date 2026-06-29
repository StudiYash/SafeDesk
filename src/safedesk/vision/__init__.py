"""SafeDesk vision foundation package."""

from safedesk.vision.camera_manager import CameraManager, CameraReadResult, CameraStatus
from safedesk.vision.compute_device import ComputeDeviceStatus, detect_compute_device
from safedesk.vision.deepface_adapter import (
    DeepFaceDependencyStatus,
    DeepFaceEmbeddingResult,
    DeepFaceVerifyResult,
    check_deepface_dependency,
    compute_face_representation,
    verify_faces,
)
from safedesk.vision.liveness_challenge import (
    LivenessChallenge,
    LivenessChallengeResult,
    LivenessChallengeStatus,
    challenge_instruction,
    create_liveness_challenge,
    describe_challenge,
    is_supported_challenge,
)
from safedesk.vision.liveness_detector import (
    FaceBox,
    LivenessDetectionResult,
    LivenessDetectionState,
    LivenessFrameObservation,
    calculate_center,
    detect_face_boxes,
    is_movement_sufficient,
    select_single_face,
    update_liveness_state,
)
from safedesk.vision.owner_manifest import (
    OwnerRegistrationManifest,
    OwnerRegistrationStatus,
    build_registration_status,
    load_owner_manifest,
    save_owner_manifest,
)
from safedesk.vision.owner_registration import OwnerSampleSaveResult, save_owner_sample
from safedesk.vision.owner_recognition import (
    OwnerRecognitionReadiness,
    OwnerRecognitionResult,
    build_recognition_readiness,
    classify_recognition_distance,
    discover_owner_sample_paths,
    verify_owner_against_samples,
)

__all__ = [
    "CameraManager",
    "CameraReadResult",
    "CameraStatus",
    "ComputeDeviceStatus",
    "DeepFaceDependencyStatus",
    "DeepFaceEmbeddingResult",
    "DeepFaceVerifyResult",
    "FaceBox",
    "LivenessChallenge",
    "LivenessChallengeResult",
    "LivenessChallengeStatus",
    "LivenessDetectionResult",
    "LivenessDetectionState",
    "LivenessFrameObservation",
    "OwnerRegistrationManifest",
    "OwnerRegistrationStatus",
    "OwnerRecognitionReadiness",
    "OwnerRecognitionResult",
    "OwnerSampleSaveResult",
    "build_registration_status",
    "build_recognition_readiness",
    "calculate_center",
    "challenge_instruction",
    "check_deepface_dependency",
    "classify_recognition_distance",
    "compute_face_representation",
    "create_liveness_challenge",
    "describe_challenge",
    "detect_compute_device",
    "detect_face_boxes",
    "discover_owner_sample_paths",
    "is_movement_sufficient",
    "is_supported_challenge",
    "load_owner_manifest",
    "save_owner_manifest",
    "save_owner_sample",
    "select_single_face",
    "update_liveness_state",
    "verify_faces",
    "verify_owner_against_samples",
]

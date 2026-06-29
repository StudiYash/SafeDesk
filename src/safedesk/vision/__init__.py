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
    "OwnerRegistrationManifest",
    "OwnerRegistrationStatus",
    "OwnerRecognitionReadiness",
    "OwnerRecognitionResult",
    "OwnerSampleSaveResult",
    "build_registration_status",
    "build_recognition_readiness",
    "check_deepface_dependency",
    "classify_recognition_distance",
    "compute_face_representation",
    "detect_compute_device",
    "discover_owner_sample_paths",
    "load_owner_manifest",
    "save_owner_manifest",
    "save_owner_sample",
    "verify_faces",
    "verify_owner_against_samples",
]

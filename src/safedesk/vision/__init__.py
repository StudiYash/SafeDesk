"""SafeDesk vision foundation package."""

from safedesk.vision.camera_manager import CameraManager, CameraReadResult, CameraStatus
from safedesk.vision.owner_manifest import (
    OwnerRegistrationManifest,
    OwnerRegistrationStatus,
    build_registration_status,
    load_owner_manifest,
    save_owner_manifest,
)
from safedesk.vision.owner_registration import OwnerSampleSaveResult, save_owner_sample

__all__ = [
    "CameraManager",
    "CameraReadResult",
    "CameraStatus",
    "OwnerRegistrationManifest",
    "OwnerRegistrationStatus",
    "OwnerSampleSaveResult",
    "build_registration_status",
    "load_owner_manifest",
    "save_owner_manifest",
    "save_owner_sample",
]

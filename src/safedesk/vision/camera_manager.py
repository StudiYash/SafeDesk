"""Manual camera access helper for owner registration."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CameraStatus:
    success: bool
    message: str


@dataclass(frozen=True)
class CameraReadResult:
    success: bool
    message: str
    frame: Any = None


class CameraManager:
    """Small wrapper around OpenCV camera capture.

    The camera is opened only when `open()` is called explicitly.
    """

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self._capture = None

    @property
    def is_opened(self) -> bool:
        return bool(self._capture is not None and self._capture.isOpened())

    def open(self) -> CameraStatus:
        try:
            import cv2
        except ImportError:
            return CameraStatus(False, "OpenCV is not installed.")

        if self.is_opened:
            return CameraStatus(True, "Camera is already open.")

        self._capture = cv2.VideoCapture(self.camera_index)
        if not self._capture.isOpened():
            self.release()
            return CameraStatus(False, "Unable to open camera.")
        return CameraStatus(True, "Camera opened.")

    def read_frame(self) -> CameraReadResult:
        if not self.is_opened:
            return CameraReadResult(False, "Camera is not open.")

        ok, frame = self._capture.read()
        if not ok or frame is None:
            return CameraReadResult(False, "Unable to read camera frame.")
        return CameraReadResult(True, "Frame captured.", frame)

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
        self._capture = None

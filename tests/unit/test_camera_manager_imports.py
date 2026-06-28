from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.vision.camera_manager import CameraManager


def test_camera_manager_imports_without_opening_camera():
    manager = CameraManager(camera_index=0)

    assert manager.is_opened is False

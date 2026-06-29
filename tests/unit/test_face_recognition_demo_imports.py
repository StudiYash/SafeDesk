from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import FACE_RECOGNITION_DEMO, SCREEN_NAMES


def test_navigation_metadata_includes_face_recognition_demo():
    assert FACE_RECOGNITION_DEMO in SCREEN_NAMES


def test_face_recognition_demo_screen_imports_without_opening_window():
    pytest.importorskip("customtkinter")

    import safedesk.gui.screens.face_recognition_demo_screen

    screen_class = safedesk.gui.screens.face_recognition_demo_screen.FaceRecognitionDemoScreen

    assert screen_class is not None
    assert hasattr(screen_class, "_run_background_operation")
    assert hasattr(screen_class, "_compute_runtime_note")
    assert hasattr(screen_class, "_set_result_display")

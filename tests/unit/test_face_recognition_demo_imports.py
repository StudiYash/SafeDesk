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


def test_recognition_log_messages_are_generic():
    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.face_recognition_demo_screen import FaceRecognitionDemoScreen

    recognized = FaceRecognitionDemoScreen.build_recognition_log_message("recognized")
    not_ready = FaceRecognitionDemoScreen.build_recognition_log_message("not_ready")
    blocked = FaceRecognitionDemoScreen.build_recognition_log_message("camera_not_ready")

    assert recognized == "Recognition demo check completed with status: recognized."
    assert not_ready == "Recognition demo check was skipped because prerequisites were not ready."
    assert blocked == "Recognition demo check was blocked because camera/frame was not ready."
    for text in (recognized, not_ready, blocked):
        assert "owner_sample_" not in text
        assert "distance" not in text.lower()
        assert "threshold" not in text.lower()

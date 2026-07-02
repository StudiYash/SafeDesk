from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import INTRUDER_DETECTION_DEMO, SCREEN_NAMES


def test_navigation_metadata_includes_intruder_detection_demo():
    assert INTRUDER_DETECTION_DEMO in SCREEN_NAMES


def test_intruder_detection_demo_screen_imports_without_opening_window():
    pytest.importorskip("customtkinter")

    import safedesk.gui.screens.intruder_detection_demo_screen

    assert safedesk.gui.screens.intruder_detection_demo_screen.IntruderDetectionDemoScreen is not None


def test_intruder_detection_log_message_helper_is_generic():
    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.intruder_detection_demo_screen import IntruderDetectionDemoScreen

    message = IntruderDetectionDemoScreen.build_intruder_check_log_message("unknown_detected")

    assert message == "Manual intruder check completed with status: unknown_detected."
    assert "path" not in message.lower()
    assert "distance" not in message.lower()
    assert "threshold" not in message.lower()


def test_intruder_detection_log_severity_warns_for_unknown_or_saved_image():
    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.intruder_detection_demo_screen import IntruderDetectionDemoScreen

    assert IntruderDetectionDemoScreen.intruder_check_log_severity("success", "owner_recognized", False) == "INFO"
    assert IntruderDetectionDemoScreen.intruder_check_log_severity("success", "unknown_detected", False) == "WARNING"
    assert IntruderDetectionDemoScreen.intruder_check_log_severity("success", "uncertain", False) == "WARNING"
    assert IntruderDetectionDemoScreen.intruder_check_log_severity("success", "owner_recognized", True) == "WARNING"


def test_intruder_detection_log_message_helper_avoids_sensitive_terms():
    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.intruder_detection_demo_screen import IntruderDetectionDemoScreen

    combined = " ".join(
        IntruderDetectionDemoScreen.build_intruder_check_log_message(result_status)
        for result_status in ("owner_recognized", "unknown_detected", "uncertain", "capture_failed", "operation_failed")
    ).lower()

    for sensitive_word in ("path", "filename", "distance", "threshold", "embedding", "exception"):
        assert sensitive_word not in combined

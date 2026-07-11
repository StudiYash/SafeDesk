from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_intruder_history_screen_imports_without_opening_window():
    import pytest

    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.intruder_history_screen import IntruderHistoryScreen

    assert IntruderHistoryScreen is not None


def test_intruder_history_screen_source_is_read_only_and_private_path_safe():
    source = (SRC / "safedesk" / "gui" / "screens" / "intruder_history_screen.py").read_text(encoding="utf-8")

    assert "IntruderHistoryReader" in source
    assert "intruder_history_opened" in source
    assert "preview_path" in source
    assert "VideoCapture(" not in source
    assert "cv2.VideoCapture" not in source
    assert "DeepFace.verify" not in source
    assert "DeepFace.find" not in source
    assert "send_email" not in source
    assert "send_otp" not in source
    assert "smtp" not in source
    assert "unlink" not in source
    assert "rmtree" not in source
    assert "requests.post" not in source
    assert "shutdown /s" not in source
    assert "Return to Launch" not in source
    assert "Return to Admin Console" not in source
    assert "Developer Return" not in source

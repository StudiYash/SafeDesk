from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_dashboard_screen_imports_without_opening_window():
    import pytest

    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.dashboard_placeholder_screen import DashboardPlaceholderScreen

    assert DashboardPlaceholderScreen is not None


def test_dashboard_screen_source_is_owner_only_read_only_summary():
    source = (SRC / "safedesk" / "gui" / "screens" / "dashboard_placeholder_screen.py").read_text(encoding="utf-8")

    assert "DashboardService" in source
    assert "dashboard_opened" in source
    assert "PublicLockScreen" not in source
    assert "VideoCapture(" not in source
    assert "DeepFace.verify" not in source
    assert "DeepFace.find" not in source
    assert "send_otp" not in source
    assert "send_email" not in source
    assert "requests.post" not in source
    assert "shutdown /s" not in source
    assert "root=context.project_root" in source

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_developer_tools_screen_imports_without_opening_window():
    import pytest

    pytest.importorskip("customtkinter")
    from safedesk.gui.screens.developer_tools_screen import DeveloperToolsScreen

    assert DeveloperToolsScreen is not None


def test_developer_tools_screen_uses_policy_and_navigation_callback_only():
    source = (SRC / "safedesk" / "gui" / "screens" / "developer_tools_screen.py").read_text(encoding="utf-8")

    assert "DeveloperToolsPolicy" in source
    assert "on_open_screen" in source
    assert "self.on_open_screen(route)" in source
    for forbidden in ("start_preview(", "VideoCapture(", "send_email", "shutdown /s", "countdown("):
        assert forbidden not in source

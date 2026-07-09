from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_admin_gate_screen_imports_without_opening_window():
    import pytest

    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.admin_gate_screen import AdminGateScreen

    assert AdminGateScreen is not None


def test_public_lock_source_still_has_no_admin_return_controls():
    source = (SRC / "safedesk" / "gui" / "screens" / "public_lock_screen.py").read_text()

    for forbidden in (
        "Return to Launch",
        "Return to Admin Console",
        "Developer Return",
        "on_return_to_launch",
        "on_return_to_admin_console",
    ):
        assert forbidden not in source

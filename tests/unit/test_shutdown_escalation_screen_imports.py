from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import SCREEN_NAMES, SHUTDOWN_ESCALATION


def test_shutdown_escalation_navigation_exists():
    assert SHUTDOWN_ESCALATION in SCREEN_NAMES


def test_shutdown_escalation_screen_imports_without_opening_window():
    import pytest

    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.shutdown_escalation_screen import ShutdownEscalationScreen

    assert ShutdownEscalationScreen is not None

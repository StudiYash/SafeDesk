from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import SCREEN_NAMES, SETUP_WIZARD


def test_navigation_metadata_includes_setup_wizard():
    assert SETUP_WIZARD in SCREEN_NAMES


def test_setup_wizard_module_imports_without_opening_window():
    pytest.importorskip("customtkinter")

    import safedesk.gui.screens.setup_wizard_screen

    assert safedesk.gui.screens.setup_wizard_screen.SetupWizardScreen is not None

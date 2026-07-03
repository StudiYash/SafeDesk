from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import PROTECTED_MODE_PREVIEW, SCREEN_DEFINITIONS, SCREEN_NAMES


def test_navigation_metadata_includes_protected_mode_demo():
    assert PROTECTED_MODE_PREVIEW in SCREEN_NAMES
    labels = {screen.name: screen.label for screen in SCREEN_DEFINITIONS}
    assert labels[PROTECTED_MODE_PREVIEW] == "Protected Mode Demo"


def test_protected_mode_screen_imports_without_opening_window():
    pytest.importorskip("customtkinter")

    import safedesk.gui.screens.protected_mode_preview_screen

    assert safedesk.gui.screens.protected_mode_preview_screen.ProtectedModePreviewScreen is not None

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import SCREEN_NAMES, THREAT_LEVEL_DEMO


def test_navigation_metadata_includes_threat_level_demo():
    assert THREAT_LEVEL_DEMO in SCREEN_NAMES


def test_threat_level_demo_screen_imports_without_opening_window():
    pytest.importorskip("customtkinter")

    import safedesk.gui.screens.threat_level_demo_screen

    assert safedesk.gui.screens.threat_level_demo_screen.ThreatLevelDemoScreen is not None

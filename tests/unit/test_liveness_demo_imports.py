from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import LIVENESS_DEMO, SCREEN_NAMES


def test_navigation_metadata_includes_liveness_demo():
    assert LIVENESS_DEMO in SCREEN_NAMES


def test_liveness_demo_enabled_helper_respects_config_flag():
    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.liveness_demo_screen import is_liveness_demo_enabled

    assert is_liveness_demo_enabled({}) is True
    assert is_liveness_demo_enabled({"enabled": True}) is True
    assert is_liveness_demo_enabled({"enabled": False}) is False


def test_start_liveness_check_respects_disabled_config_without_window():
    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.liveness_demo_screen import LivenessDemoScreen

    class FakeLabel:
        def __init__(self):
            self.text = ""

        def configure(self, **kwargs):
            self.text = kwargs.get("text", self.text)

    class FakeBanner:
        def __init__(self):
            self.message = ""

        def set_message(self, message):
            self.message = message

    dummy = SimpleNamespace(
        liveness_config={"enabled": False},
        camera=SimpleNamespace(is_opened=True),
        challenge=object(),
        liveness_active=True,
        operation_label=FakeLabel(),
        message_banner=FakeBanner(),
        result_label=FakeLabel(),
    )

    LivenessDemoScreen.start_liveness_check(dummy)

    assert dummy.challenge is None
    assert dummy.liveness_active is False
    assert dummy.operation_label.text == "Operation: idle"
    assert "disabled in configuration" in dummy.message_banner.message
    assert "liveness.enabled is false" in dummy.result_label.text


def test_liveness_demo_screen_imports_without_opening_window():
    pytest.importorskip("customtkinter")

    import safedesk.gui.screens.liveness_demo_screen

    assert safedesk.gui.screens.liveness_demo_screen.LivenessDemoScreen is not None

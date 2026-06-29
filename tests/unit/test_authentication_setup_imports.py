from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import AUTHENTICATION_SETUP, SCREEN_NAMES


def test_navigation_metadata_includes_authentication_setup():
    assert AUTHENTICATION_SETUP in SCREEN_NAMES


def test_authentication_setup_screen_imports_without_opening_window():
    pytest.importorskip("customtkinter")

    import safedesk.gui.screens.authentication_setup_screen

    assert safedesk.gui.screens.authentication_setup_screen.AuthenticationSetupScreen is not None


def test_master_password_verification_message_uses_full_label():
    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.authentication_setup_screen import AuthenticationSetupScreen

    message = AuthenticationSetupScreen._verification_message("Master Password", "failed", "Secret did not match.", 2)

    assert message == "Master Password: not verified. Attempts remaining: 2."

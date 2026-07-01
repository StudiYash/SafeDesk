from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.navigation import OWNER_FACE_REGISTRATION, SCREEN_NAMES


def test_navigation_metadata_includes_owner_face_registration():
    assert OWNER_FACE_REGISTRATION in SCREEN_NAMES


def test_owner_face_registration_screen_imports_without_opening_window():
    pytest.importorskip("customtkinter")

    import safedesk.gui.screens.owner_face_registration_screen

    assert safedesk.gui.screens.owner_face_registration_screen.OwnerFaceRegistrationScreen is not None


def test_owner_registration_log_messages_are_generic():
    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.owner_face_registration_screen import OwnerFaceRegistrationScreen

    failed = OwnerFaceRegistrationScreen.build_owner_registration_log_message("failed")
    blocked = OwnerFaceRegistrationScreen.build_owner_registration_log_message("blocked")

    assert failed == "Owner sample capture completed with status: failed."
    assert blocked == "Owner sample capture was blocked because camera/frame was not ready."
    assert "owner_sample_" not in failed
    assert ".jpg" not in failed

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_phase_16_screen_modules_import_without_opening_window():
    import pytest

    pytest.importorskip("customtkinter")

    from safedesk.gui.screens.launch_screen import LaunchScreen
    from safedesk.gui.screens.public_lock_screen import PublicLockScreen

    assert LaunchScreen is not None
    assert PublicLockScreen is not None

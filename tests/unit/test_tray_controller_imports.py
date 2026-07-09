from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.background_agent import TrayController


class MissingPystrayController(TrayController):
    def _load_pystray_module(self):
        return None


def test_tray_controller_imports_without_pystray_or_gui_window():
    controller = MissingPystrayController(
        dispatch_to_gui=lambda callback: callback(),
        on_open_safedesk=lambda: None,
        on_open_admin_console=lambda: None,
        on_lock_safedesk=lambda: None,
        on_exit_safedesk=lambda: None,
    )

    result = controller.start()

    assert result.success is False
    assert result.status == "unavailable"
    assert result.tray_available is False
    assert result.tray_running is False


def test_tray_controller_source_uses_gui_dispatch_callbacks():
    source = (SRC / "safedesk" / "background_agent" / "tray_controller.py").read_text(encoding="utf-8")

    assert "dispatch_to_gui" in source
    assert "_menu_open_safedesk" in source
    assert "_menu_open_admin_console" in source
    assert "_menu_lock_safedesk" in source
    assert "_menu_exit_safedesk" in source

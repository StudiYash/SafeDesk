from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.global_shortcut import WindowsHotkeyController


def test_windows_hotkey_controller_imports_without_windows_registration():
    controller = WindowsHotkeyController(
        hotkey="ctrl+alt+l",
        dispatch_to_gui=lambda callback: callback(),
        on_shortcut_pressed=lambda: None,
        platform_name="Linux",
    )

    result = controller.start()

    assert result.success is False
    assert result.status == "unavailable"
    assert result.registered is False
    assert result.available is False


def test_windows_hotkey_controller_rejects_invalid_hotkey_safely():
    controller = WindowsHotkeyController(
        hotkey="ctrl+shift+l",
        dispatch_to_gui=lambda callback: callback(),
        on_shortcut_pressed=lambda: None,
        platform_name="Windows",
    )

    result = controller.start()

    assert result.success is False
    assert result.status == "unsupported_hotkey"
    assert result.registered is False


def test_windows_hotkey_controller_stop_is_safe_when_not_running():
    controller = WindowsHotkeyController(
        hotkey="ctrl+alt+l",
        dispatch_to_gui=lambda callback: callback(),
        on_shortcut_pressed=lambda: None,
        platform_name="Linux",
    )

    result = controller.stop()

    assert result.success is True
    assert result.status == "not_running"


def test_windows_hotkey_controller_uses_registered_hotkey_api_and_gui_dispatch():
    source = (SRC / "safedesk" / "global_shortcut" / "windows_hotkey_controller.py").read_text(encoding="utf-8")

    assert "RegisterHotKey" in source
    assert "UnregisterHotKey" in source
    assert "PostThreadMessageW" in source
    assert "dispatch_to_gui" in source
    assert "SetWindowsHookEx" not in source
    assert "BlockInput" not in source
    assert "pynput" not in source
    assert "import keyboard" not in source
    assert "GetAsyncKeyState" not in source
    assert "GetKeyState" not in source

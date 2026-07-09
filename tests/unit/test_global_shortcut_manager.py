from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.global_shortcut.shortcut_manager import GlobalShortcutManager, parse_hotkey


def test_parse_hotkey_accepts_supported_phase_20_shortcut():
    result = parse_hotkey(" Ctrl + Alt + L ")

    assert result.success is True
    assert result.normalized_hotkey == "ctrl+alt+l"
    assert result.modifiers != 0
    assert result.virtual_key != 0


def test_parse_hotkey_rejects_unsupported_shortcut():
    result = parse_hotkey("ctrl+shift+l")

    assert result.success is False
    assert result.status == "unsupported_hotkey"


def test_global_shortcut_manager_attempts_registration_on_windows():
    manager = GlobalShortcutManager(DEFAULT_CONFIG, platform_name="Windows")

    status = manager.build_status(registered=True, available=True)

    assert manager.should_attempt_registration() is True
    assert status.supported_platform is True
    assert status.hotkey_supported is True
    assert status.activation_action == "public_lock"
    assert status.message == "Global shortcut is registered."


def test_global_shortcut_manager_reports_unavailable_off_windows():
    manager = GlobalShortcutManager(DEFAULT_CONFIG, platform_name="Linux")

    status = manager.build_status()

    assert manager.should_attempt_registration() is False
    assert status.supported_platform is False
    assert status.available is False
    assert status.message == "Global shortcut support is unavailable on this platform."


def test_global_shortcut_manager_disabled_config_does_not_attempt_registration():
    config = deep_merge(DEFAULT_CONFIG, {"global_shortcut": {"enabled": False}})
    manager = GlobalShortcutManager(config, platform_name="Windows")

    status = manager.build_status()

    assert manager.should_attempt_registration() is False
    assert status.enabled is False
    assert status.message == "Global shortcut foundation is disabled."


def test_global_shortcut_manager_invalid_hotkey_does_not_attempt_registration():
    config = deep_merge(DEFAULT_CONFIG, {"global_shortcut": {"hotkey": "ctrl+alt+x"}})
    manager = GlobalShortcutManager(config, platform_name="Windows")

    status = manager.build_status()

    assert manager.should_attempt_registration() is False
    assert status.hotkey_supported is False


def test_global_shortcut_config_has_no_startup_or_admin_action_fields():
    shortcut_config = DEFAULT_CONFIG["global_shortcut"]

    assert "startup" not in shortcut_config
    assert "start_with_windows" not in shortcut_config
    assert "registry" not in shortcut_config
    assert "service" not in shortcut_config
    assert shortcut_config["activation_action"] == "public_lock"

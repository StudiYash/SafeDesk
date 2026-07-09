from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.background_agent import BackgroundAgentManager
from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG


def test_background_agent_manager_builds_enabled_status():
    manager = BackgroundAgentManager(DEFAULT_CONFIG)

    status = manager.build_status(tray_available=True, tray_running=True)

    assert manager.should_attempt_tray() is True
    assert status.enabled is True
    assert status.foundation_enabled is True
    assert status.demo_only is True
    assert status.system_tray_enabled is True
    assert status.tray_available is True
    assert status.tray_running is True
    assert status.message == "System tray support is running."


def test_background_agent_manager_disabled_config_is_safe():
    config = deep_merge(DEFAULT_CONFIG, {"background_agent": {"enabled": False}})
    manager = BackgroundAgentManager(config)

    status = manager.build_status()

    assert manager.should_attempt_tray() is False
    assert status.enabled is False
    assert status.tray_running is False
    assert status.message == "Background agent foundation is disabled."


def test_background_agent_manager_tray_disabled_does_not_attempt_tray():
    config = deep_merge(DEFAULT_CONFIG, {"background_agent": {"system_tray_enabled": False}})
    manager = BackgroundAgentManager(config)

    status = manager.build_status()

    assert manager.should_attempt_tray() is False
    assert status.system_tray_enabled is False
    assert status.message == "System tray support is disabled."


def test_background_agent_config_has_no_startup_persistence_fields():
    background_config = DEFAULT_CONFIG["background_agent"]

    assert "startup" not in background_config
    assert "start_with_windows" not in background_config
    assert "registry" not in background_config
    assert "service" not in background_config

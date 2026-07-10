from pathlib import Path
import inspect
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.lockdown_display import DisplayBounds, LockdownDisplayManager


class FakeRoot:
    def winfo_screenwidth(self):
        return 1280

    def winfo_screenheight(self):
        return 720


class FakeInteractiveWindow:
    created = []

    def __init__(self, _root, _context, display, _config, _on_development_escape):
        self.display = display
        self.shown = False
        self.destroyed = False
        FakeInteractiveWindow.created.append(self)

    def show(self):
        self.shown = True

    def destroy(self):
        self.destroyed = True


class FakeBlackoutWindow:
    created = []

    def __init__(self, _root, _context, display, _config, _on_development_escape):
        self.display = display
        self.shown = False
        self.destroyed = False
        FakeBlackoutWindow.created.append(self)

    def show(self):
        self.shown = True

    def destroy(self):
        self.destroyed = True


def _manager(config=None, display_provider=None, primary_window_factory=FakeInteractiveWindow, blackout_window_factory=FakeBlackoutWindow):
    FakeInteractiveWindow.created = []
    FakeBlackoutWindow.created = []
    return LockdownDisplayManager(
        config or DEFAULT_CONFIG,
        display_provider=display_provider,
        primary_window_factory=primary_window_factory,
        blackout_window_factory=blackout_window_factory,
    )


def test_lockdown_display_manager_builds_safe_default_status():
    manager = _manager()

    status = manager.build_status()

    assert status.enabled is True
    assert status.foundation_enabled is True
    assert status.demo_only is True
    assert status.fullscreen_enabled is True
    assert status.active is False


def test_lockdown_display_manager_uses_separate_primary_and_blackout_factories():
    source = (SRC / "safedesk" / "lockdown_display" / "display_manager.py").read_text(encoding="utf-8")
    generic_factory_name = "window" + "_factory"

    assert "primary_window_factory" in source
    assert "blackout_window_factory" in source
    assert generic_factory_name not in inspect.signature(LockdownDisplayManager).parameters


def test_disabled_lockdown_display_does_not_start():
    config = deep_merge(DEFAULT_CONFIG, {"lockdown_display": {"enabled": False}})
    manager = _manager(config)

    result = manager.start(FakeRoot(), object())

    assert result.success is False
    assert result.status == "disabled"
    assert manager.active is False


def test_fallback_primary_display_uses_root_dimensions():
    manager = _manager(display_provider=lambda: [])

    displays = manager.detect_displays(FakeRoot())

    assert len(displays) == 1
    assert displays[0].width == 1280
    assert displays[0].height == 720
    assert displays[0].primary is True


def test_windows_monitor_detection_is_preferred_before_screeninfo():
    manager = _manager()
    manager._detect_with_windows_ctypes = lambda: [
        DisplayBounds(index=0, x=1920, y=0, width=1920, height=1080, primary=False),
        DisplayBounds(index=1, x=0, y=0, width=1920, height=1080, primary=True),
    ]
    manager._detect_with_screeninfo = lambda: [
        DisplayBounds(index=0, x=0, y=0, width=9999, height=9999, primary=True),
    ]

    displays = manager.detect_displays(FakeRoot())

    assert len(displays) == 2
    assert displays[0].primary is True
    assert displays[0].x == 0
    assert displays[1].x == 1920


def test_screeninfo_is_preferred_when_windows_bounds_look_dpi_scaled():
    manager = _manager()
    manager._detect_with_windows_ctypes = lambda: [
        DisplayBounds(index=0, x=0, y=0, width=1280, height=720, primary=True),
        DisplayBounds(index=1, x=0, y=1080, width=1920, height=515, primary=False),
        DisplayBounds(index=2, x=1920, y=0, width=1280, height=720, primary=False),
    ]
    manager._detect_with_screeninfo = lambda: [
        DisplayBounds(index=0, x=0, y=0, width=1920, height=1080, primary=True),
        DisplayBounds(index=1, x=0, y=1080, width=1920, height=515, primary=False),
        DisplayBounds(index=2, x=1920, y=0, width=1920, height=1080, primary=False),
    ]

    displays = manager.detect_displays(FakeRoot())

    assert len(displays) == 3
    assert displays[0].width == 1920
    assert displays[0].height == 1080
    assert displays[2].x == 1920
    assert displays[2].width == 1920


def test_windows_bounds_are_used_when_screeninfo_is_unavailable():
    manager = _manager()
    manager._detect_with_windows_ctypes = lambda: [
        DisplayBounds(index=0, x=0, y=0, width=1280, height=720, primary=True),
        DisplayBounds(index=1, x=1280, y=0, width=1280, height=720, primary=False),
    ]
    manager._detect_with_screeninfo = lambda: []

    displays = manager.detect_displays(FakeRoot())

    assert len(displays) == 2
    assert displays[0].width == 1280
    assert displays[1].x == 1280


def test_negative_monitor_coordinates_are_preserved():
    displays = (
        DisplayBounds(index=0, x=-1920, y=0, width=1920, height=1080, primary=False),
        DisplayBounds(index=1, x=0, y=0, width=1920, height=1080, primary=True),
    )
    manager = _manager(display_provider=lambda: displays)

    detected = manager.detect_displays(FakeRoot())

    assert any(display.x == -1920 for display in detected)
    assert any(display.y == 0 for display in detected)


def test_primary_fallback_remains_single_display_even_if_root_reports_wide_desktop():
    class WideRoot:
        def winfo_screenwidth(self):
            return 3840

        def winfo_screenheight(self):
            return 1080

    manager = _manager(display_provider=lambda: [])

    displays = manager.detect_displays(WideRoot())

    assert len(displays) == 1
    assert displays[0].width == 3840
    assert displays[0].height == 1080
    assert displays[0].primary is True


def test_display_count_is_capped_by_max_display_windows():
    config = deep_merge(DEFAULT_CONFIG, {"lockdown_display": {"max_display_windows": 2}})
    displays = tuple(DisplayBounds(index=index, x=index * 100, y=0, width=100, height=100, primary=index == 0) for index in range(4))
    manager = _manager(config, display_provider=lambda: displays)

    detected = manager.detect_displays(FakeRoot())

    assert len(detected) == 2


def test_start_creates_windows_and_duplicate_start_is_already_active():
    displays = (
        DisplayBounds(index=0, x=0, y=0, width=100, height=100, primary=True),
        DisplayBounds(index=1, x=-100, y=0, width=100, height=100, primary=False),
    )
    manager = _manager(display_provider=lambda: displays)

    result = manager.start(FakeRoot(), object())
    duplicate = manager.start(FakeRoot(), object())

    assert result.success is True
    assert result.window_count == 2
    assert duplicate.success is True
    assert duplicate.status == "already_active"
    assert len(FakeInteractiveWindow.created) == 1
    assert len(FakeBlackoutWindow.created) == 1
    assert FakeInteractiveWindow.created[0].display == displays[0]
    assert FakeBlackoutWindow.created[0].display == displays[1]
    assert FakeInteractiveWindow.created[0].shown is True
    assert FakeBlackoutWindow.created[0].shown is True


def test_single_display_creates_only_primary_interactive_window():
    displays = (DisplayBounds(index=0, x=0, y=0, width=100, height=100, primary=True),)
    manager = _manager(display_provider=lambda: displays)

    result = manager.start(FakeRoot(), object())

    assert result.success is True
    assert result.window_count == 1
    assert len(FakeInteractiveWindow.created) == 1
    assert len(FakeBlackoutWindow.created) == 0
    assert FakeInteractiveWindow.created[0].display == displays[0]


def test_start_creates_one_window_per_selected_screeninfo_display():
    manager = _manager()
    screeninfo_displays = [
        DisplayBounds(index=0, x=0, y=0, width=1920, height=1080, primary=True),
        DisplayBounds(index=1, x=0, y=1080, width=1920, height=515, primary=False),
        DisplayBounds(index=2, x=1920, y=0, width=1920, height=1080, primary=False),
    ]
    manager._detect_with_windows_ctypes = lambda: [
        DisplayBounds(index=0, x=0, y=0, width=1280, height=720, primary=True),
        DisplayBounds(index=1, x=0, y=1080, width=1920, height=515, primary=False),
        DisplayBounds(index=2, x=1920, y=0, width=1280, height=720, primary=False),
    ]
    manager._detect_with_screeninfo = lambda: screeninfo_displays

    result = manager.start(FakeRoot(), object())

    assert result.success is True
    assert result.window_count == 3
    assert [window.display for window in FakeInteractiveWindow.created] == [screeninfo_displays[0]]
    assert [window.display for window in FakeBlackoutWindow.created] == screeninfo_displays[1:]


def test_stop_is_safe_when_inactive_and_clears_active_state():
    displays = (
        DisplayBounds(index=0, x=0, y=0, width=100, height=100, primary=True),
        DisplayBounds(index=1, x=100, y=0, width=100, height=100, primary=False),
    )
    manager = _manager(display_provider=lambda: displays)

    inactive = manager.stop()
    manager.start(FakeRoot(), object())
    active_stop = manager.stop()

    assert inactive.success is True
    assert inactive.status == "not_active"
    assert active_stop.success is True
    assert active_stop.status == "stopped"
    assert manager.active is False
    assert FakeInteractiveWindow.created[0].destroyed is True
    assert FakeBlackoutWindow.created[0].destroyed is True

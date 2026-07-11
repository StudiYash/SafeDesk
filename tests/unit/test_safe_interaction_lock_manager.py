from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.interaction_lock import SafeInteractionLockManager


class FakeRoot:
    def __init__(self):
        self.after_calls = []
        self.cancelled = []

    def after(self, milliseconds, callback):
        after_id = f"after-{len(self.after_calls) + 1}"
        self.after_calls.append((after_id, milliseconds, callback))
        return after_id

    def after_cancel(self, after_id):
        self.cancelled.append(after_id)


class FakeWindow:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.recovered = 0
        self.focus_requests = []
        self.lift_requests = []
        self.topmost_requests = []

    def recover_visual_priority(self, *, focus_primary=False, lift_window=True, reapply_topmost=True):
        if self.fail:
            raise RuntimeError("safe test failure")
        self.recovered += 1
        self.focus_requests.append(focus_primary)
        self.lift_requests.append(lift_window)
        self.topmost_requests.append(reapply_topmost)
        return True


def _manager(config=None, windows=(), events=None):
    return SafeInteractionLockManager(
        config or DEFAULT_CONFIG,
        window_provider=lambda: windows,
        event_callback=(lambda action, message, metadata: events.append((action, message, metadata))) if events is not None else None,
    )


def test_safe_interaction_lock_manager_starts_and_schedules_recovery():
    root = FakeRoot()
    events = []
    windows = (FakeWindow(),)
    manager = _manager(windows=windows, events=events)

    result = manager.start(root)

    assert result.success is True
    assert result.status == "started"
    assert manager.active is True
    assert len(root.after_calls) == 1
    assert root.after_calls[0][1] == 2000
    assert events[0][0] == "safe_interaction_lock_started"


def test_safe_interaction_lock_manager_refuses_when_disabled():
    config = deep_merge(DEFAULT_CONFIG, {"safe_interaction_lock": {"enabled": False}})
    root = FakeRoot()
    manager = _manager(config=config)

    result = manager.start(root)

    assert result.success is False
    assert result.status == "disabled"
    assert manager.active is False
    assert root.after_calls == []


def test_safe_interaction_lock_manager_refuses_when_focus_recovery_disabled():
    config = deep_merge(DEFAULT_CONFIG, {"safe_interaction_lock": {"focus_recovery_enabled": False}})
    root = FakeRoot()
    manager = _manager(config=config, windows=(FakeWindow(),))

    result = manager.start(root)

    assert result.success is False
    assert result.status == "disabled"
    assert manager.active is False
    assert root.after_calls == []


def test_duplicate_start_does_not_create_duplicate_timer():
    root = FakeRoot()
    manager = _manager(windows=(FakeWindow(),))

    first = manager.start(root)
    duplicate = manager.start(root)

    assert first.success is True
    assert duplicate.success is True
    assert duplicate.status == "already_active"
    assert len(root.after_calls) == 1


def test_stop_cancels_timer_and_is_safe_when_inactive():
    root = FakeRoot()
    manager = _manager(windows=(FakeWindow(),))

    inactive = manager.stop()
    manager.start(root)
    active = manager.stop()

    assert inactive.success is True
    assert inactive.status == "not_active"
    assert active.success is True
    assert active.status == "stopped"
    assert manager.active is False
    assert root.cancelled == ["after-1"]


def test_recover_once_calls_windows_and_swallows_failures():
    windows = (FakeWindow(), FakeWindow(fail=True), FakeWindow())
    manager = _manager(windows=windows)

    result = manager.recover_once(focus_primary=True)

    assert result.success is True
    assert result.window_count == 2
    assert windows[0].focus_requests == [True]
    assert windows[1].focus_requests == []
    assert windows[2].focus_requests == [False]


def test_recover_once_respects_lift_and_topmost_flags():
    config = deep_merge(
        DEFAULT_CONFIG,
        {"safe_interaction_lock": {"lift_windows_on_recovery": False, "reapply_topmost_on_recovery": False}},
    )
    window = FakeWindow()
    manager = _manager(config=config, windows=(window,))

    manager.recover_once()

    assert window.lift_requests == [False]
    assert window.topmost_requests == [False]


def test_periodic_tick_recovers_and_reschedules_without_tick_logging():
    root = FakeRoot()
    events = []
    window = FakeWindow()
    manager = _manager(windows=(window,), events=events)

    manager.start(root)
    first_callback = root.after_calls[0][2]
    first_callback()

    assert manager.tick_count == 1
    assert window.recovered == 1
    assert len(root.after_calls) == 2
    assert [event[0] for event in events] == ["safe_interaction_lock_started"]


def test_build_status_reports_safe_state():
    window = FakeWindow()
    manager = _manager(windows=(window,))

    status = manager.build_status()

    assert status.enabled is True
    assert status.foundation_enabled is True
    assert status.demo_only is True
    assert status.active is False
    assert status.focus_recovery_enabled is True


def test_interaction_lock_sources_do_not_add_hooks_persistence_or_shutdown():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for folder in (SRC / "safedesk" / "interaction_lock", SRC / "safedesk" / "lockdown_display")
        for path in folder.glob("*.py")
    )
    forbidden = (
        "SetWindowsHookEx",
        "BlockInput",
        "pynput",
        "import keyboard",
        "GetAsyncKeyState",
        "GetKeyState",
        "winreg",
        "schtasks",
        "Start Menu\\\\Programs\\\\Startup",
        "RunOnce",
        "Windows Service",
        "shutdown /s",
        "shutdown.exe",
        "os.system(\"shutdown",
        "attributes(\"-fullscreen\", True)",
    )

    for text in forbidden:
        assert text not in combined

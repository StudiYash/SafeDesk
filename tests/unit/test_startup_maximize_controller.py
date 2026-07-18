from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.gui.startup_maximize import (
    STARTUP_MAXIMIZE_MAX_ATTEMPTS,
    StartupMaximizeController,
)


class FakeWindow:
    def __init__(self, *, mapped=False, accept_after=1):
        self.mapped = mapped
        self.accept_after = accept_after
        self.map_callback = None
        self.after_callbacks = []
        self.after_delays = []
        self.cancelled = []
        self.unbound = []
        self.update_idletasks_calls = 0
        self.maximize_requests = 0

    def bind(self, sequence, callback, add=None):
        assert sequence == "<Map>"
        assert add == "+"
        self.map_callback = callback
        return "map-binding"

    def unbind(self, sequence, binding_id):
        self.unbound.append((sequence, binding_id))

    def winfo_ismapped(self):
        return self.mapped

    def after(self, delay, callback):
        self.after_delays.append(delay)
        self.after_callbacks.append(callback)
        return f"after-{len(self.after_callbacks)}"

    def after_cancel(self, after_id):
        self.cancelled.append(after_id)

    def update_idletasks(self):
        self.update_idletasks_calls += 1

    def wm_state(self, requested=None):
        if requested is not None:
            assert requested == "zoomed"
            self.maximize_requests += 1
        if self.accept_after is not None and self.maximize_requests >= self.accept_after:
            return "zoomed"
        return "normal"

    def trigger_map(self):
        assert self.map_callback is not None
        self.mapped = True
        self.map_callback(SimpleNamespace(widget=self))

    def run_next_after(self):
        callback = self.after_callbacks.pop(0)
        callback()


def test_false_setting_does_not_bind_or_schedule_maximization():
    window = FakeWindow()
    controller = StartupMaximizeController(window, requested=False)

    assert controller.arm() is False
    assert window.map_callback is None
    assert window.after_callbacks == []
    assert window.maximize_requests == 0


def test_true_setting_waits_for_map_then_requests_normal_zoomed_state():
    window = FakeWindow(accept_after=1)
    controller = StartupMaximizeController(window, requested=True)

    assert controller.arm() is True
    assert window.after_callbacks == []
    window.trigger_map()
    assert len(window.after_callbacks) == 1
    assert window.after_delays == [100]

    window.run_next_after()
    assert len(window.after_callbacks) == 1
    window.run_next_after()

    assert controller.attempt_count == 1
    assert window.update_idletasks_calls == 1
    assert window.maximize_requests == 1
    assert window.after_callbacks == []


def test_maximize_retries_are_bounded():
    window = FakeWindow(accept_after=None)
    controller = StartupMaximizeController(window, requested=True)
    controller.arm()
    window.trigger_map()

    while window.after_callbacks:
        window.run_next_after()

    assert controller.attempt_count == STARTUP_MAXIMIZE_MAX_ATTEMPTS
    assert window.maximize_requests == STARTUP_MAXIMIZE_MAX_ATTEMPTS
    assert window.after_callbacks == []


def test_destroying_window_prevents_pending_retry_work():
    destroying = {"value": False}
    window = FakeWindow(accept_after=None)
    controller = StartupMaximizeController(
        window,
        requested=True,
        destroying=lambda: destroying["value"],
    )
    controller.arm()
    window.trigger_map()
    window.run_next_after()
    assert controller.attempt_count == 1
    assert len(window.after_callbacks) == 1

    destroying["value"] = True
    window.run_next_after()

    assert controller.attempt_count == 1
    assert window.maximize_requests == 1
    assert window.after_callbacks == []


def test_cancel_removes_pending_callback_and_is_repeatable():
    window = FakeWindow(mapped=True)
    controller = StartupMaximizeController(window, requested=True)
    controller.arm()
    controller.cancel()
    controller.cancel()

    assert window.cancelled == ["after-1"]


def test_startup_maximize_source_uses_no_fullscreen_or_os_level_shortcuts():
    source = (SRC / "safedesk" / "gui" / "startup_maximize.py").read_text(encoding="utf-8")

    for forbidden in (
        'attributes("-fullscreen"',
        'attributes("-topmost"',
        "winfo_screenwidth",
        "winfo_screenheight",
        "subprocess",
        "os.system",
        "winreg",
        "ctypes",
    ):
        assert forbidden not in source
    assert 'wm_state("zoomed")' in source

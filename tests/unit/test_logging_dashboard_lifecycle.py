from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

ctk = pytest.importorskip("customtkinter")

import safedesk.gui.screens.logging_dashboard_screen as dashboard_module
from safedesk.gui.screens.logging_dashboard_screen import LoggingDashboardScreen
from safedesk.logging.log_models import EventLogResult


class FakeButton:
    def __init__(self):
        self.state = "normal"

    def configure(self, **kwargs):
        self.state = kwargs.get("state", self.state)


class FakeBanner:
    def __init__(self):
        self.message = ""

    def set_message(self, message):
        self.message = message


class FakeThread:
    starts = 0

    def __init__(self, *, target, daemon):
        self.target = target
        self.daemon = daemon

    def start(self):
        FakeThread.starts += 1


def _clear_screen_state():
    buttons = [FakeButton() for _ in range(4)]
    state = SimpleNamespace(
        _clear_in_progress=False,
        clear_logs_confirmation_pending=True,
        clear_button=buttons[0],
        refresh_button=buttons[1],
        previous_button=buttons[2],
        next_button=buttons[3],
        message_banner=FakeBanner(),
        _clear_events_worker=lambda: None,
        _clear_thread=None,
        _screen_active=True,
        _clear_poll_after_id=None,
    )
    state._set_clear_controls_enabled = lambda enabled: LoggingDashboardScreen._set_clear_controls_enabled(state, enabled)
    state._schedule_clear_poll = lambda: None
    return state, buttons


def test_duplicate_clear_start_is_ignored_and_controls_disable(monkeypatch):
    FakeThread.starts = 0
    monkeypatch.setattr(dashboard_module, "Thread", FakeThread)
    screen, buttons = _clear_screen_state()

    LoggingDashboardScreen._begin_clear_operation(screen)
    LoggingDashboardScreen._begin_clear_operation(screen)

    assert FakeThread.starts == 1
    assert screen._clear_in_progress is True
    assert all(button.state == "disabled" for button in buttons)
    assert screen.message_banner.message == "Clearing local events..."


def test_release_is_repeatable_and_resume_can_restart_result_polling():
    cancelled = []
    scheduled = []
    screen = SimpleNamespace(
        _screen_active=True,
        clear_logs_confirmation_pending=True,
        _clear_poll_after_id="after-1",
        _clear_in_progress=True,
        after_cancel=lambda after_id: cancelled.append(after_id),
        _schedule_clear_poll=lambda: scheduled.append(True),
        _update_pagination_controls=lambda: None,
    )

    LoggingDashboardScreen.release_resources(screen)
    LoggingDashboardScreen.release_resources(screen)
    LoggingDashboardScreen.resume_resources(screen)

    assert cancelled == ["after-1"]
    assert screen._screen_active is True
    assert scheduled == [True]


def test_completion_after_release_skips_widgets_and_success_resets_page():
    released = SimpleNamespace(_screen_active=False)
    LoggingDashboardScreen._complete_clear_operation(
        released,
        EventLogResult(True, "cleared", "Local event logs cleared."),
    )

    refreshed = []
    screen, buttons = _clear_screen_state()
    screen._clear_in_progress = True
    screen._clear_thread = object()
    screen.search_var = SimpleNamespace(set=lambda value: None)
    screen.category_var = SimpleNamespace(set=lambda value: None)
    screen.status_var = SimpleNamespace(set=lambda value: None)
    screen.severity_var = SimpleNamespace(set=lambda value: None)
    screen.action_var = SimpleNamespace(set=lambda value: None)
    screen.source_var = SimpleNamespace(set=lambda value: None)
    screen.sort_field_var = SimpleNamespace(set=lambda value: None)
    screen.sort_direction_var = SimpleNamespace(set=lambda value: None)
    screen.current_page = 4
    screen.total_event_count = 200
    screen.refresh_logs = lambda **kwargs: refreshed.append(kwargs)
    screen._update_pagination_controls = lambda: None

    LoggingDashboardScreen._complete_clear_operation(
        screen,
        EventLogResult(True, "cleared", "Local event logs cleared."),
    )

    assert screen._clear_in_progress is False
    assert screen.current_page == 0
    assert screen.total_event_count == 0
    assert refreshed == [{"reset_clear_confirmation": False, "reset_page": True}]
    assert screen.message_banner.message == "Local event logs cleared."


def test_clear_failure_recovers_controls_with_generic_message():
    recovered = []
    screen, _buttons = _clear_screen_state()
    screen._clear_in_progress = True
    screen._clear_thread = object()
    screen._update_pagination_controls = lambda: recovered.append(True)

    LoggingDashboardScreen._complete_clear_operation(
        screen,
        EventLogResult(False, "storage_error", "Local event logs could not be cleared."),
    )

    assert screen._clear_in_progress is False
    assert recovered == [True]
    assert screen.message_banner.message == "Local event logs could not be cleared."
    assert "sqlite" not in screen.message_banner.message.lower()

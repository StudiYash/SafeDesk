from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_alarm_system_screen_imports_without_opening_window():
    import pytest

    pytest.importorskip("customtkinter")
    from safedesk.gui.screens.alarm_system_screen import AlarmSystemScreen

    assert AlarmSystemScreen is not None


def test_alarm_system_screen_has_manual_controls_and_cleanup_only():
    source = (SRC / "safedesk" / "gui" / "screens" / "alarm_system_screen.py").read_text(encoding="utf-8")

    assert "SafeAlarmPreviewManager" in source
    assert "Play Safe Preview" in source
    assert "Stop Preview" in source
    assert "Refresh Status" in source
    assert "def release_resources" in source
    assert "result = self.manager.release_resources()" in source
    assert "start_preview(self)" in source
    assert "_released" not in source
    assert 'if action == "alarm_preview_timed_out":' in source
    for forbidden in (
        "Video" + "Capture(",
        "DeepFace." + "verify",
        "send_" + "email",
        "shutdown" + " /s",
        "Block" + "Input",
        "win" + "reg",
        "requests." + "post",
    ):
        assert forbidden not in source


def test_alarm_system_release_is_reusable_and_timeout_refresh_stays_enabled():
    import pytest

    pytest.importorskip("customtkinter")
    from safedesk.alarm import AlarmPreviewOperationResult
    from safedesk.gui.screens.alarm_system_screen import AlarmSystemScreen

    class FakeManager:
        def __init__(self):
            self.preview_active = True
            self.release_calls = 0

        def release_resources(self):
            self.release_calls += 1
            was_active = self.preview_active
            self.preview_active = False
            message = "Safe alarm preview stopped." if was_active else "No alarm preview is active."
            return AlarmPreviewOperationResult(True, "cleanup", message, False, "local_audio")

    class FakeBanner:
        def __init__(self):
            self.messages = []

        def set_message(self, message):
            self.messages.append(message)

    class FakeLogger:
        def log_app_event(self, **kwargs):
            return None

    screen = object.__new__(AlarmSystemScreen)
    screen.manager = FakeManager()
    screen.message_banner = FakeBanner()
    screen.event_logger = FakeLogger()
    refresh_calls = []
    screen.refresh_status = lambda: refresh_calls.append(screen.manager.preview_active)

    screen.release_resources()
    assert screen.manager.preview_active is False
    assert screen.manager.release_calls == 1
    assert refresh_calls[-1] is False

    screen.manager.preview_active = True
    screen.release_resources()
    assert screen.manager.preview_active is False
    assert screen.manager.release_calls == 2
    assert refresh_calls[-1] is False

    screen._log_preview_event(
        "alarm_preview_timed_out",
        "Safe alarm preview reached its time limit.",
        {"result_status": "timeout"},
    )
    assert screen.message_banner.messages[-1] == "Safe alarm preview reached its time limit."
    assert len(refresh_calls) == 3

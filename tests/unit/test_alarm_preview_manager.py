from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.alarm import SafeAlarmPreviewManager
from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG


class FakeRoot:
    def __init__(self):
        self.callbacks = {}
        self.cancelled = []
        self.counter = 0

    def after(self, milliseconds, callback):
        self.counter += 1
        timer_id = f"after-{self.counter}"
        self.callbacks[timer_id] = (milliseconds, callback)
        return timer_id

    def after_cancel(self, timer_id):
        self.cancelled.append(timer_id)
        self.callbacks.pop(timer_id, None)


class FakeBackend:
    name = "fake_audio"

    def __init__(self, *, available=True, wav_success=True, beep_success=True):
        self.available = available
        self.wav_success = wav_success
        self.beep_success = beep_success
        self.wav_calls = 0
        self.beep_calls = 0
        self.stop_calls = 0

    def is_available(self):
        return self.available

    def play_wav(self, path):
        self.wav_calls += 1
        return self.wav_success

    def play_beep(self):
        self.beep_calls += 1
        return self.beep_success

    def stop(self):
        self.stop_calls += 1
        return True


def _config(**alarm):
    return deep_merge(DEFAULT_CONFIG, {"alarm": alarm})


def _make_wav(tmp_path):
    path = tmp_path / "assets" / "audio" / "preview.wav"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"RIFF")
    return path


def test_manual_preview_works_while_real_alarm_enabled_flag_remains_false(tmp_path):
    backend = FakeBackend()
    manager = SafeAlarmPreviewManager(_config(audio_file=""), root=tmp_path, backend=backend)

    result = manager.start_preview(FakeRoot())

    assert DEFAULT_CONFIG["alarm"]["enabled"] is False
    assert result.status == "preview_completed"
    assert result.used_fallback is True
    assert backend.beep_calls == 1
    assert manager.preview_active is False


def test_safe_wav_is_preferred_and_schedules_one_hard_stop(tmp_path):
    _make_wav(tmp_path)
    root = FakeRoot()
    backend = FakeBackend()
    manager = SafeAlarmPreviewManager(_config(audio_file="preview.wav"), root=tmp_path, backend=backend)

    result = manager.start_preview(root)

    assert result.status == "preview_started"
    assert manager.preview_active is True
    assert backend.wav_calls == 1
    assert backend.beep_calls == 0
    assert len(root.callbacks) == 1
    assert next(iter(root.callbacks.values()))[0] == 5000


def test_missing_or_failed_wav_uses_one_beep_fallback(tmp_path):
    missing_backend = FakeBackend()
    missing = SafeAlarmPreviewManager(_config(audio_file="missing.wav"), root=tmp_path, backend=missing_backend)
    missing_result = missing.start_preview(FakeRoot())

    _make_wav(tmp_path)
    failed_backend = FakeBackend(wav_success=False)
    failed = SafeAlarmPreviewManager(_config(audio_file="preview.wav"), root=tmp_path, backend=failed_backend)
    failed_result = failed.start_preview(FakeRoot())

    assert missing_result.used_fallback is True
    assert missing_backend.beep_calls == 1
    assert failed_result.used_fallback is True
    assert failed_backend.wav_calls == 1
    assert failed_backend.beep_calls == 1


def test_duplicate_start_manual_stop_timeout_and_release_are_safe(tmp_path):
    _make_wav(tmp_path)
    root = FakeRoot()
    backend = FakeBackend()
    manager = SafeAlarmPreviewManager(_config(audio_file="preview.wav"), root=tmp_path, backend=backend)

    first = manager.start_preview(root)
    timer_id, (_, timeout_callback) = next(iter(root.callbacks.items()))
    duplicate = manager.start_preview(root)

    assert first.success is True
    assert duplicate.status == "already_active"
    assert backend.wav_calls == 1
    assert len(root.callbacks) == 1

    stopped = manager.stop_preview()
    assert stopped.success is True
    assert timer_id in root.cancelled
    assert backend.stop_calls == 1
    assert manager.stop_preview().status == "not_active"

    manager.start_preview(root)
    _, timeout_callback = next(iter(root.callbacks.values()))
    timeout_callback()
    assert manager.preview_active is False
    assert backend.stop_calls == 2

    manager.start_preview(root)
    manager.release_resources()
    assert manager.preview_active is False
    assert backend.stop_calls == 3


def test_unsafe_runtime_modes_refuse_preview(tmp_path):
    cases = (
        {"foundation_enabled": False},
        {"manual_preview_enabled": False},
        {"demo_only": False},
        {"automatic_trigger_enabled": True},
        {"allow_looping": True},
    )
    for overrides in cases:
        backend = FakeBackend()
        manager = SafeAlarmPreviewManager(_config(**overrides), root=tmp_path, backend=backend)
        result = manager.start_preview(FakeRoot())
        assert result.success is False
        assert backend.wav_calls == 0
        assert backend.beep_calls == 0


def test_backend_unavailable_and_event_metadata_are_safe(tmp_path):
    events = []
    manager = SafeAlarmPreviewManager(
        _config(audio_file="missing.wav"),
        root=tmp_path,
        backend=FakeBackend(available=False),
        event_callback=lambda action, message, metadata: events.append((action, message, metadata)),
    )

    result = manager.start_preview(FakeRoot())
    serialized = repr(events)

    assert result.status == "unavailable"
    assert str(tmp_path) not in serialized
    assert "missing.wav" not in serialized
    assert all("exception" not in metadata for _, _, metadata in events)


def test_manager_defensively_clamps_duration_and_advisory_volume():
    manager = SafeAlarmPreviewManager(
        _config(max_preview_duration_seconds=999, volume=5.0),
        backend=FakeBackend(),
    )

    assert manager.max_preview_duration_seconds == 10
    assert manager.configured_volume == 1.0

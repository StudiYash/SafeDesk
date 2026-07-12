"""Owner-controlled lifecycle manager for short local alarm previews."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from safedesk.alarm.alarm_models import AlarmPreviewOperationResult, AlarmPreviewStatus
from safedesk.alarm.alarm_path_policy import AlarmAudioPathResolution, resolve_alarm_audio_path
from safedesk.alarm.windows_audio_backend import WindowsAudioPreviewBackend


class SafeAlarmPreviewManager:
    """Run only explicit, short, non-looping owner preview actions."""

    def __init__(
        self,
        config: dict,
        *,
        root: Path | None = None,
        backend: Any | None = None,
        event_callback: Callable[[str, str, dict], None] | None = None,
    ):
        self.config = config if isinstance(config, dict) else {}
        raw_alarm = self.config.get("alarm", {})
        self.alarm_config = raw_alarm if isinstance(raw_alarm, dict) else {}
        self.root = root
        self.backend = backend or WindowsAudioPreviewBackend()
        self.event_callback = event_callback
        self._root_widget: Any | None = None
        self._after_id: Any | None = None
        self._preview_active = False

    @property
    def preview_active(self) -> bool:
        return self._preview_active

    def build_status(self) -> AlarmPreviewStatus:
        resolution = self._audio_resolution()
        backend_available = self._backend_available()
        if self.preview_active:
            message = "A safe WAV preview is active."
        elif not self._preview_allowed():
            message = self._preview_blocked_message()
        elif resolution.available and backend_available:
            message = "A safe local WAV preview is ready."
        elif self.beep_fallback_enabled and backend_available:
            message = "A single short system beep is ready as the preview fallback."
        else:
            message = "Alarm preview audio is unavailable."
        return AlarmPreviewStatus(
            enabled=self.alarm_config.get("enabled", False) is True,
            foundation_enabled=self.foundation_enabled,
            demo_only=self.demo_only,
            manual_preview_enabled=self.manual_preview_enabled,
            automatic_trigger_enabled=self.automatic_trigger_enabled,
            allow_looping=self.allow_looping,
            preview_active=self.preview_active,
            audio_configured=resolution.configured,
            audio_available=resolution.available,
            beep_fallback_enabled=self.beep_fallback_enabled,
            backend_available=backend_available,
            max_preview_duration_seconds=self.max_preview_duration_seconds,
            configured_volume=self.configured_volume,
            message=message,
        )

    @property
    def foundation_enabled(self) -> bool:
        return self.alarm_config.get("foundation_enabled", True) is True

    @property
    def demo_only(self) -> bool:
        return self.alarm_config.get("demo_only", True) is True

    @property
    def manual_preview_enabled(self) -> bool:
        return self.alarm_config.get("manual_preview_enabled", True) is True

    @property
    def automatic_trigger_enabled(self) -> bool:
        return self.alarm_config.get("automatic_trigger_enabled", False) is True

    @property
    def allow_looping(self) -> bool:
        return self.alarm_config.get("allow_looping", False) is True

    @property
    def beep_fallback_enabled(self) -> bool:
        return self.alarm_config.get("beep_fallback_enabled", True) is True

    @property
    def max_preview_duration_seconds(self) -> int:
        value = self.alarm_config.get("max_preview_duration_seconds", 5)
        if isinstance(value, bool) or not isinstance(value, int):
            return 5
        return min(10, max(1, value))

    @property
    def configured_volume(self) -> float:
        value = self.alarm_config.get("volume", 0.5)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return 0.5
        return min(1.0, max(0.0, float(value)))

    def start_preview(self, root_widget: Any) -> AlarmPreviewOperationResult:
        """Start one explicit preview, preferring a safe local WAV."""

        self._emit_event("alarm_preview_requested", "A manual alarm preview was requested.", self._metadata("requested"))
        if self.preview_active:
            return self._skipped("already_active", "A safe alarm preview is already active.")
        if not self._preview_allowed():
            return self._skipped("blocked", self._preview_blocked_message())
        if not self._backend_available():
            return self._unavailable("Alarm preview audio is unavailable on this system.")

        resolution = self._audio_resolution()
        if resolution.available and resolution.path is not None and self._play_wav(resolution.path):
            self._root_widget = root_widget
            self._preview_active = True
            if not self._schedule_timeout():
                self._stop_backend()
                self._preview_active = False
                self._root_widget = None
                return self._unavailable("Alarm preview could not start safely.")
            result = AlarmPreviewOperationResult(
                True,
                "preview_started",
                "Safe WAV preview started. Use Stop Preview to end it early.",
                True,
                self._backend_name(),
                False,
                self.max_preview_duration_seconds,
            )
            self._emit_event("alarm_preview_started", result.message, self._metadata(result.status, result=result))
            return result

        if self.beep_fallback_enabled and self._play_beep():
            result = AlarmPreviewOperationResult(
                True,
                "preview_completed",
                "Safe one-time beep preview completed.",
                False,
                self._backend_name(),
                True,
                0,
            )
            self._emit_event("alarm_preview_completed", result.message, self._metadata(result.status, result=result))
            return result

        return self._unavailable("Alarm preview audio is unavailable.")

    def stop_preview(self, reason: str = "manual") -> AlarmPreviewOperationResult:
        """Stop current playback and cancel its hard-stop timer safely."""

        was_active = self.preview_active
        self._cancel_timeout()
        if was_active:
            self._stop_backend()
        self._preview_active = False
        self._root_widget = None
        if not was_active:
            return AlarmPreviewOperationResult(True, "not_active", "No alarm preview is active.", False, self._backend_name())

        action = "alarm_preview_timed_out" if reason == "timeout" else "alarm_preview_stopped"
        message = "Safe alarm preview reached its time limit." if reason == "timeout" else "Safe alarm preview stopped."
        result = AlarmPreviewOperationResult(True, reason, message, False, self._backend_name())
        self._emit_event(action, message, self._metadata(reason, result=result))
        return result

    def release_resources(self) -> AlarmPreviewOperationResult:
        """Stop playback and timer during screen or application cleanup."""

        was_active = self.preview_active
        result = self.stop_preview(reason="cleanup")
        if was_active:
            self._emit_event("alarm_preview_cleanup", "Alarm preview resources were released.", self._metadata("cleanup"))
        return result

    def _handle_timeout(self) -> None:
        self._after_id = None
        if self.preview_active:
            self.stop_preview(reason="timeout")

    def _schedule_timeout(self) -> bool:
        if self._root_widget is None or self._after_id is not None:
            return False
        try:
            self._after_id = self._root_widget.after(
                self.max_preview_duration_seconds * 1000,
                self._handle_timeout,
            )
            return self._after_id is not None
        except Exception:
            self._after_id = None
            return False

    def _cancel_timeout(self) -> bool:
        after_id = self._after_id
        self._after_id = None
        if after_id is None or self._root_widget is None:
            return False
        try:
            self._root_widget.after_cancel(after_id)
            return True
        except Exception:
            return False

    def _preview_allowed(self) -> bool:
        return (
            self.foundation_enabled
            and self.demo_only
            and self.manual_preview_enabled
            and not self.automatic_trigger_enabled
            and not self.allow_looping
        )

    def _preview_blocked_message(self) -> str:
        if not self.foundation_enabled:
            return "Alarm preview foundation is disabled."
        if not self.demo_only:
            return "Alarm preview requires demo-only mode."
        if not self.manual_preview_enabled:
            return "Manual alarm preview is disabled."
        if self.automatic_trigger_enabled or self.allow_looping:
            return "Alarm preview configuration is not safe for Phase 24."
        return "Alarm preview is unavailable."

    def _audio_resolution(self) -> AlarmAudioPathResolution:
        try:
            return resolve_alarm_audio_path(self.config, self.root)
        except Exception:
            return AlarmAudioPathResolution(False, False, False, None, "unavailable", "Configured preview audio is unavailable.")

    def _backend_available(self) -> bool:
        try:
            return self.backend.is_available() is True
        except Exception:
            return False

    def _backend_name(self) -> str:
        name = str(getattr(self.backend, "name", "local_audio"))
        return "windows_standard_audio" if name == "windows_standard_audio" else "local_audio"

    def _play_wav(self, path: Path) -> bool:
        try:
            return self.backend.play_wav(path) is True
        except Exception:
            return False

    def _play_beep(self) -> bool:
        try:
            return self.backend.play_beep() is True
        except Exception:
            return False

    def _stop_backend(self) -> bool:
        try:
            return self.backend.stop() is True
        except Exception:
            return False

    def _skipped(self, status: str, message: str) -> AlarmPreviewOperationResult:
        result = AlarmPreviewOperationResult(False, status, message, self.preview_active, self._backend_name())
        self._emit_event("alarm_preview_start_skipped", message, self._metadata(status, result=result))
        return result

    def _unavailable(self, message: str) -> AlarmPreviewOperationResult:
        result = AlarmPreviewOperationResult(False, "unavailable", message, False, self._backend_name())
        self._emit_event("alarm_preview_unavailable", message, self._metadata(result.status, result=result))
        return result

    def _metadata(self, result_status: str, *, result: AlarmPreviewOperationResult | None = None) -> dict:
        resolution = self._audio_resolution()
        return {
            "result_status": result_status,
            "preview_active": self.preview_active if result is None else result.preview_active,
            "backend": self._backend_name(),
            "used_fallback": False if result is None else result.used_fallback,
            "duration_seconds": 0 if result is None else result.duration_seconds,
            "audio_configured": resolution.configured,
            "audio_available": resolution.available,
        }

    def _emit_event(self, action: str, message: str, metadata: dict) -> None:
        if self.event_callback is None:
            return
        try:
            self.event_callback(action, message, dict(metadata))
        except Exception:
            pass

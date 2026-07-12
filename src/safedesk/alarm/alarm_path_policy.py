"""Path policy for optional local SafeDesk WAV preview files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

from safedesk.storage.paths import project_root


@dataclass(frozen=True)
class AlarmAudioPathResolution:
    """Internal path resolution result; the path is never used as display text."""

    configured: bool
    safe: bool
    available: bool
    path: Path | None
    status: str
    message: str


def _is_absolute_path_text(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return Path(normalized).is_absolute() or PureWindowsPath(value).is_absolute() or normalized.startswith("//")


def _parts(value: str) -> tuple[str, ...]:
    return tuple(part for part in value.replace("\\", "/").split("/") if part not in {"", "."})


def resolve_alarm_audio_path(config: dict, root: Path | None = None) -> AlarmAudioPathResolution:
    """Resolve a configured WAV only when it remains inside the allowed local directory."""

    alarm = config.get("alarm", {}) if isinstance(config, dict) else {}
    if not isinstance(alarm, dict):
        return AlarmAudioPathResolution(False, False, False, None, "invalid_config", "Alarm preview configuration is unavailable.")

    raw_audio_file = alarm.get("audio_file", "")
    if not isinstance(raw_audio_file, str) or not raw_audio_file.strip():
        return AlarmAudioPathResolution(False, True, False, None, "not_configured", "No local WAV preview is configured.")

    raw_allowed_dir = alarm.get("allowed_audio_dir", "assets/audio")
    if not isinstance(raw_allowed_dir, str) or not raw_allowed_dir.strip():
        return AlarmAudioPathResolution(True, False, False, None, "unsafe_path", "Configured preview audio is unavailable.")
    if _is_absolute_path_text(raw_allowed_dir) or ".." in _parts(raw_allowed_dir) or not _parts(raw_allowed_dir):
        return AlarmAudioPathResolution(True, False, False, None, "unsafe_path", "Configured preview audio is unavailable.")
    if _is_absolute_path_text(raw_audio_file) or ".." in _parts(raw_audio_file):
        return AlarmAudioPathResolution(True, False, False, None, "unsafe_path", "Configured preview audio is unavailable.")
    if Path(raw_audio_file.replace("\\", "/")).suffix.lower() != ".wav":
        return AlarmAudioPathResolution(True, False, False, None, "unsupported_format", "Configured preview audio is unavailable.")

    base_root = (root or project_root()).resolve()
    allowed_dir = (base_root / Path(*_parts(raw_allowed_dir))).resolve()
    try:
        allowed_dir.relative_to(base_root)
    except ValueError:
        return AlarmAudioPathResolution(True, False, False, None, "unsafe_path", "Configured preview audio is unavailable.")
    audio_parts = _parts(raw_audio_file)
    allowed_parts = _parts(raw_allowed_dir)
    if len(audio_parts) >= len(allowed_parts) and audio_parts[: len(allowed_parts)] == allowed_parts:
        candidate = (base_root / Path(*audio_parts)).resolve()
    else:
        candidate = (allowed_dir / Path(*audio_parts)).resolve()

    try:
        candidate.relative_to(allowed_dir)
    except ValueError:
        return AlarmAudioPathResolution(True, False, False, None, "unsafe_path", "Configured preview audio is unavailable.")

    if not candidate.is_file():
        return AlarmAudioPathResolution(True, True, False, None, "missing", "Configured preview audio is unavailable.")
    return AlarmAudioPathResolution(True, True, True, candidate, "available", "Configured preview audio is available.")

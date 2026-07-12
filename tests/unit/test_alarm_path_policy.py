from pathlib import Path
import os
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.alarm.alarm_path_policy import resolve_alarm_audio_path
from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG


def _config(audio_file: str):
    return deep_merge(DEFAULT_CONFIG, {"alarm": {"audio_file": audio_file, "allowed_audio_dir": "assets/audio"}})


def test_empty_audio_file_is_safely_unconfigured(tmp_path):
    result = resolve_alarm_audio_path(_config(""), tmp_path)

    assert result.configured is False
    assert result.path is None
    assert str(tmp_path) not in result.message


def test_safe_existing_and_missing_wav_resolution(tmp_path):
    audio_dir = tmp_path / "assets" / "audio"
    audio_dir.mkdir(parents=True)
    wav = audio_dir / "preview.wav"
    wav.write_bytes(b"RIFF")

    existing = resolve_alarm_audio_path(_config("preview.wav"), tmp_path)
    missing = resolve_alarm_audio_path(_config("missing.wav"), tmp_path)

    assert existing.safe is True
    assert existing.available is True
    assert existing.path == wav.resolve()
    assert missing.safe is True
    assert missing.available is False
    assert missing.path is None
    assert str(tmp_path) not in missing.message


@pytest.mark.parametrize("value", ("../outside.wav", "/tmp/outside.wav", r"C:\Users\owner\outside.wav", "preview.mp3"))
def test_unsafe_or_unsupported_audio_paths_are_rejected(tmp_path, value):
    result = resolve_alarm_audio_path(_config(value), tmp_path)

    assert result.safe is False
    assert result.path is None
    assert str(tmp_path) not in result.message


def test_symlink_resolving_outside_allowed_directory_is_rejected(tmp_path):
    audio_dir = tmp_path / "assets" / "audio"
    audio_dir.mkdir(parents=True)
    outside = tmp_path / "outside.wav"
    outside.write_bytes(b"RIFF")
    link = audio_dir / "linked.wav"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is unavailable in this environment.")

    result = resolve_alarm_audio_path(_config("linked.wav"), tmp_path)

    assert result.safe is False
    assert result.path is None


def test_allowed_directory_symlink_outside_project_root_is_rejected(tmp_path):
    outside_root = tmp_path.parent / f"{tmp_path.name}-outside-audio"
    outside_root.mkdir(exist_ok=True)
    (outside_root / "preview.wav").write_bytes(b"RIFF")
    assets = tmp_path / "assets"
    assets.mkdir()
    link = assets / "audio"
    try:
        os.symlink(outside_root, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Directory symlink creation is unavailable in this environment.")

    result = resolve_alarm_audio_path(_config("preview.wav"), tmp_path)

    assert result.safe is False
    assert result.path is None

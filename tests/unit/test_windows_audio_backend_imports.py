from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_windows_audio_backend_imports_without_playing_audio():
    from safedesk.alarm.windows_audio_backend import WindowsAudioPreviewBackend

    assert WindowsAudioPreviewBackend is not None
    assert callable(WindowsAudioPreviewBackend.stop)


def test_windows_audio_backend_is_guarded_non_looping_and_standard_library_only():
    source = (SRC / "safedesk" / "alarm" / "windows_audio_backend.py").read_text(encoding="utf-8")

    assert "import winsound" in source
    assert "SND_ASYNC" in source
    assert "SND_FILENAME" in source
    assert "MessageBeep" in source
    for forbidden in (
        "SND_" + "LOOP",
        "sub" + "process",
        "os." + "system",
        "shell=" + "True",
        "start" + "file",
        "ff" + "play",
        "pygame." + "mixer",
        "play" + "sound",
        "simple" + "audio",
        "py" + "dub",
        "py" + "caw",
        "SetMaster" + "Volume",
    ):
        assert forbidden not in source

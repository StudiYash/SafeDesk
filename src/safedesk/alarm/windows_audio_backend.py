"""Windows standard-library backend for short SafeDesk alarm previews."""

from __future__ import annotations

from pathlib import Path
import platform


class WindowsAudioPreviewBackend:
    """Play one non-looping WAV or one short system beep on Windows."""

    name = "windows_standard_audio"

    def is_available(self) -> bool:
        if platform.system() != "Windows":
            return False
        try:
            import winsound

            return winsound is not None
        except Exception:
            return False

    def play_wav(self, path: Path) -> bool:
        if not self.is_available():
            return False
        try:
            import winsound

            flags = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
            winsound.PlaySound(str(path), flags)
            return True
        except Exception:
            return False

    def play_beep(self) -> bool:
        if not self.is_available():
            return False
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            return True
        except Exception:
            return False

    def stop(self) -> bool:
        if not self.is_available():
            return False
        try:
            import winsound

            winsound.PlaySound(None, 0)
            return True
        except Exception:
            return False

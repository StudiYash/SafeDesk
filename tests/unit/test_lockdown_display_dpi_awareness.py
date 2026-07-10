from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.lockdown_display.dpi_awareness import enable_windows_dpi_awareness


def test_dpi_awareness_helper_is_safe_on_non_windows():
    with patch("sys.platform", "linux"):
        assert enable_windows_dpi_awareness() is False

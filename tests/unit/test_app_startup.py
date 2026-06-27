from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.app.application import load_runtime_context, run_config_check
from safedesk.utils.constants import SUPPORTED_SECURITY_MODES


def test_check_config_path_runs_through_app_layer():
    assert run_config_check() == 0


def test_runtime_context_is_valid_for_safe_startup_config():
    context = load_runtime_context()

    assert context.report.is_valid is True
    assert context.settings.security_mode in SUPPORTED_SECURITY_MODES
    assert context.settings.demo_safe_mode is True
    assert context.settings.real_email_enabled is False
    assert context.settings.real_shutdown_enabled is False
    assert context.settings.real_lockdown_enabled is False
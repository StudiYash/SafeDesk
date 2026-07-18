from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.developer_tools import DeveloperToolsDiagnostics


class FakeBackend:
    def __init__(self, available):
        self.available = available

    def is_available(self):
        return self.available


def test_safe_diagnostics_are_generic_and_path_free():
    summary = DeveloperToolsDiagnostics(
        DEFAULT_CONFIG,
        configuration_valid=True,
        alarm_backend=FakeBackend(False),
    ).build_summary()
    values = "\n".join(f"{item.label}: {item.value}" for item in summary.items)

    assert "Configuration validation: valid" in values
    assert "Alarm backend: unavailable" in values
    assert str(ROOT) not in values
    for forbidden in ("USERNAME", "COMPUTERNAME", "monitor", "hardware", "exception"):
        assert forbidden.lower() not in values.lower()


def test_diagnostics_hidden_returns_no_items():
    config = {**DEFAULT_CONFIG, "developer_tools": {**DEFAULT_CONFIG["developer_tools"], "show_runtime_diagnostics": False}}
    summary = DeveloperToolsDiagnostics(config).build_summary()

    assert summary.items == ()


def test_production_effective_environment_blocks_diagnostics():
    summary = DeveloperToolsDiagnostics(
        DEFAULT_CONFIG,
        effective_environment="production",
        alarm_backend=FakeBackend(True),
    ).build_summary()

    assert summary.items == ()
    assert "hidden" in summary.message.lower()

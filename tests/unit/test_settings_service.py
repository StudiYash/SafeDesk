from dataclasses import replace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.config.env_loader import load_environment
from safedesk.settings import SettingsService


def test_settings_service_exposes_typed_snapshot_status_and_safe_save(tmp_path):
    service = SettingsService(
        DEFAULT_CONFIG,
        load_environment(environ={}),
        configuration_valid=True,
        root=tmp_path,
    )
    snapshot = service.current_snapshot()
    status = service.build_status()

    assert snapshot.max_recent_events == 50
    assert status.configuration_valid is True
    assert status.managed_setting_count == 13
    result = service.save(replace(snapshot, retention_days=45))
    assert result.success and result.changed_setting_count == 1
    assert "saved locally and verified" in result.message.lower()
    assert str(tmp_path) not in result.message

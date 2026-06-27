from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge, load_config
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.config.env_loader import load_environment
from safedesk.config.setup_state import get_setup_status, is_owner_profile_configured, is_setup_complete
from safedesk.config.validators import validate_config


def test_setup_status_incomplete_by_default():
    result = load_config(root=ROOT)
    env = load_environment(environ={})
    status = get_setup_status(DEFAULT_CONFIG, result, env)

    assert status.setup_completed is False
    assert status.owner_name_configured is False
    assert status.face_registration_status == "pending"


def test_setup_status_complete_with_owner_name():
    config = deep_merge(
        DEFAULT_CONFIG,
        {
            "setup": {"completed": True},
            "owner_profile": {"owner_name": "Local Owner"},
        },
    )
    result = load_config(root=ROOT)
    status = get_setup_status(config, result, load_environment(environ={}))

    assert is_setup_complete(config) is True
    assert is_owner_profile_configured(config) is True
    assert status.setup_completed is True
    assert status.owner_name_configured is True


def test_basic_owner_email_validation():
    valid_config = deep_merge(DEFAULT_CONFIG, {"owner_profile": {"owner_email": "owner@example.com"}})
    invalid_config = deep_merge(DEFAULT_CONFIG, {"owner_profile": {"owner_email": "owner@example"}})

    assert validate_config(valid_config, load_environment(environ={}), root=ROOT).is_valid is True

    invalid_report = validate_config(invalid_config, load_environment(environ={}), root=ROOT)
    assert invalid_report.is_valid is False
    assert "invalid_owner_email_format" in {issue.code for issue in invalid_report.errors}

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.config.env_loader import load_environment
from safedesk.config.validators import validate_config


def _report_for(owner_registration_config):
    config = deep_merge(DEFAULT_CONFIG, {"owner_face_registration": owner_registration_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_invalid_owner_registration_required_samples_rejected():
    report = _report_for({"required_samples": 0})

    assert report.is_valid is False
    assert "invalid_positive_integer" in {issue.code for issue in report.errors}


def test_invalid_owner_registration_camera_index_rejected():
    report = _report_for({"camera_index": -1})

    assert report.is_valid is False
    assert "invalid_owner_registration_camera_index" in {issue.code for issue in report.errors}


def test_invalid_owner_registration_format_rejected():
    report = _report_for({"image_format": "bmp"})

    assert report.is_valid is False
    assert "invalid_owner_registration_image_format" in {issue.code for issue in report.errors}


def test_face_recognition_must_remain_disabled():
    config = deep_merge(DEFAULT_CONFIG, {"face_recognition": {"enabled": True}})
    report = validate_config(config, load_environment(environ={}), root=ROOT)

    assert report.is_valid is False
    assert "face_recognition_not_enabled_in_phase_6" in {issue.code for issue in report.errors}

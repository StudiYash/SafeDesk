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


def _report_for(liveness_config):
    config = deep_merge(DEFAULT_CONFIG, {"liveness": liveness_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_liveness_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)

    assert report.is_valid is True


def test_liveness_demo_only_false_is_rejected():
    report = _report_for({"demo_only": False})

    assert report.is_valid is False
    assert "liveness_demo_only_required" in {issue.code for issue in report.errors}


def test_invalid_liveness_duration_rejected():
    report = _report_for({"challenge_duration_seconds": 0})

    assert report.is_valid is False
    assert "invalid_positive_integer" in {issue.code for issue in report.errors}


def test_invalid_liveness_movement_threshold_rejected():
    report = _report_for({"movement_threshold_ratio": 0})

    assert report.is_valid is False
    assert "invalid_liveness_movement_threshold" in {issue.code for issue in report.errors}


def test_invalid_liveness_camera_index_rejected():
    report = _report_for({"camera_index": True})

    assert report.is_valid is False
    assert "invalid_liveness_camera_index" in {issue.code for issue in report.errors}

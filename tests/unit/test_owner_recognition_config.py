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


def _report_for(owner_recognition_config):
    config = deep_merge(DEFAULT_CONFIG, {"owner_recognition": owner_recognition_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_invalid_owner_recognition_model_rejected():
    report = _report_for({"model_name": "OtherModel"})

    assert report.is_valid is False
    assert "unsupported_owner_recognition_model" in {issue.code for issue in report.errors}


def test_invalid_owner_recognition_metric_rejected():
    report = _report_for({"distance_metric": "manhattan"})

    assert report.is_valid is False
    assert "unsupported_owner_recognition_metric" in {issue.code for issue in report.errors}


def test_invalid_owner_recognition_threshold_rejected():
    report = _report_for({"demo_threshold": 3})

    assert report.is_valid is False
    assert "invalid_number_range" in {issue.code for issue in report.errors}

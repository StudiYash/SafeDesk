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


def _report_for(intruder_config):
    config = deep_merge(DEFAULT_CONFIG, {"intruder_detection": intruder_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_intruder_detection_config_is_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)

    assert report.is_valid is True


def test_intruder_demo_only_false_is_rejected():
    report = _report_for({"demo_only": False})

    assert report.is_valid is False
    assert "intruder_detection_demo_only_required" in {issue.code for issue in report.errors}


def test_intruder_capture_unknown_only_false_is_rejected():
    report = _report_for({"capture_unknown_only": False})

    assert report.is_valid is False
    assert "intruder_capture_unknown_only_required" in {issue.code for issue in report.errors}


def test_absolute_intruder_paths_are_rejected():
    report = _report_for(
        {
            "intruder_images_dir": str(ROOT / "data" / "intruders"),
            "manifest_path": str(ROOT / "data" / "config" / "intruder_capture_manifest.json"),
        }
    )

    assert report.is_valid is False
    assert "absolute_relative_path" in {issue.code for issue in report.errors}


def test_invalid_intruder_image_format_is_rejected():
    report = _report_for({"image_format": "bmp"})

    assert report.is_valid is False
    assert "invalid_intruder_detection_image_format" in {issue.code for issue in report.errors}


def test_invalid_intruder_image_quality_is_rejected():
    report = _report_for({"image_quality": 101})

    assert report.is_valid is False
    assert "invalid_intruder_detection_image_quality" in {issue.code for issue in report.errors}


def test_intruder_boolean_numeric_fields_are_rejected():
    report = _report_for({"camera_index": True, "minimum_owner_samples_required": False})

    assert report.is_valid is False
    codes = {issue.code for issue in report.errors}
    assert "invalid_intruder_detection_camera_index" in codes
    assert "invalid_positive_integer" in codes

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


def _report_for(ui_config):
    config = deep_merge(DEFAULT_CONFIG, {"ui": ui_config})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_invalid_ui_width_is_rejected():
    report = _report_for({"window_width": 0})

    assert report.is_valid is False
    assert "invalid_positive_integer" in {issue.code for issue in report.errors}


def test_invalid_ui_theme_is_rejected():
    report = _report_for({"theme": "neon"})

    assert report.is_valid is False
    assert "unsupported_ui_theme" in {issue.code for issue in report.errors}


def test_empty_color_theme_is_rejected():
    report = _report_for({"color_theme": ""})

    assert report.is_valid is False
    assert "invalid_ui_color_theme" in {issue.code for issue in report.errors}

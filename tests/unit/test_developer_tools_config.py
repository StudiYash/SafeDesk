from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.config.env_loader import load_environment
from safedesk.config.validators import validate_config


def _report_for(overrides):
    return validate_config(
        deep_merge(DEFAULT_CONFIG, {"developer_tools": overrides}),
        load_environment(environ={}),
        root=ROOT,
    )


def test_default_developer_tools_config_matches_example_and_validates():
    example = json.loads((ROOT / "config.example.json").read_text(encoding="utf-8"))
    expected = {
        "enabled": True,
        "demo_only": True,
        "show_demo_screens": True,
        "show_runtime_diagnostics": True,
    }

    assert DEFAULT_CONFIG["developer_tools"] == expected
    assert example["developer_tools"] == expected
    assert validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT).is_valid


def test_developer_tools_section_and_boolean_fields_are_validated():
    invalid_section = validate_config(
        deep_merge(DEFAULT_CONFIG, {"developer_tools": "enabled"}),
        load_environment(environ={}),
        root=ROOT,
    )
    invalid_flags = _report_for(
        {
            "enabled": 1,
            "demo_only": "yes",
            "show_demo_screens": 1,
            "show_runtime_diagnostics": "yes",
        }
    )

    assert "invalid_developer_tools_section" in {issue.code for issue in invalid_section.errors}
    assert "invalid_developer_tools_boolean" in {issue.code for issue in invalid_flags.errors}


def test_developer_tools_demo_only_false_is_rejected_but_visibility_flags_may_be_false():
    assert "developer_tools_demo_only_required" in {
        issue.code for issue in _report_for({"demo_only": False}).errors
    }
    assert _report_for({"enabled": False}).is_valid
    assert _report_for({"show_demo_screens": False}).is_valid
    assert _report_for({"show_runtime_diagnostics": False}).is_valid

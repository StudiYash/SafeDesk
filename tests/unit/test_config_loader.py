import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import load_config
from safedesk.config.exceptions import SafeDeskConfigFileError


def test_config_example_loads_correctly(tmp_path):
    example = tmp_path / "config.example.json"
    example.write_text(
        json.dumps(
            {
                "app": {"name": "SafeDesk", "demo_safe_mode": True},
                "security_mode": {"default_mode": "demo_safe"},
            }
        ),
        encoding="utf-8",
    )

    result = load_config(root=tmp_path, example_path=example)

    assert result.config["app"]["name"] == "SafeDesk"
    assert result.config["security_mode"]["default_mode"] == "demo_safe"
    assert result.local_config_loaded is False
    assert example in result.loaded_files


def test_local_config_missing_does_not_fail(tmp_path):
    result = load_config(root=tmp_path)

    assert result.local_config_loaded is False
    assert result.config["app"]["name"] == "SafeDesk"


def test_invalid_json_raises_clear_error(tmp_path):
    example = tmp_path / "config.example.json"
    example.write_text("{ invalid json", encoding="utf-8")

    with pytest.raises(SafeDeskConfigFileError, match="Invalid JSON"):
        load_config(root=tmp_path, example_path=example)

from dataclasses import replace
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.app.application import load_runtime_context
from safedesk.config import load_config
from safedesk.config.env_loader import load_environment
from safedesk.settings import SettingsService, managed_snapshot_from_config


def test_saved_settings_reload_through_the_startup_path(tmp_path):
    example_path = tmp_path / "config.example.json"
    example_content = "{}\n"
    example_path.write_text(example_content, encoding="utf-8")
    local_path = tmp_path / "config.local.json"
    local_path.write_text(
        json.dumps(
            {
                "alarm": {"audio_file": "preview.wav"},
                "owner_profile": {"owner_name": "Preserved"},
            }
        ),
        encoding="utf-8",
    )
    initial = load_config(root=tmp_path).config
    service = SettingsService(
        initial,
        load_environment(env_file=tmp_path / ".env", environ={}),
        root=tmp_path,
    )
    snapshot = replace(
        managed_snapshot_from_config(initial),
        start_maximized=True,
        retention_days=91,
        show_demo_screens=False,
        global_shortcut_enabled=False,
    )

    result = service.save(snapshot)
    reloaded = load_config(root=tmp_path).config
    runtime = load_runtime_context(root=tmp_path)
    local_data = json.loads(local_path.read_text(encoding="utf-8"))

    assert result.success is True
    assert local_path.exists()
    assert reloaded["ui"]["start_maximized"] is True
    assert reloaded["logging"]["retention_days"] == 91
    assert reloaded["developer_tools"]["show_demo_screens"] is False
    assert reloaded["global_shortcut"]["shortcut_enabled"] is False
    assert runtime.load_result.config["ui"]["start_maximized"] is True
    assert runtime.load_result.config["logging"]["retention_days"] == 91
    assert local_data["alarm"]["audio_file"] == "preview.wav"
    assert local_data["owner_profile"] == {"owner_name": "Preserved"}
    assert example_path.read_text(encoding="utf-8") == example_content


def test_settings_and_startup_ignore_the_current_working_directory(tmp_path, monkeypatch):
    runtime_root = tmp_path / "runtime-root"
    other_root = tmp_path / "other-working-directory"
    runtime_root.mkdir()
    other_root.mkdir()
    (runtime_root / "config.example.json").write_text("{}", encoding="utf-8")
    initial = load_config(root=runtime_root).config
    service = SettingsService(
        initial,
        load_environment(env_file=runtime_root / ".env", environ={}),
        root=runtime_root,
    )
    snapshot = replace(managed_snapshot_from_config(initial), retention_days=72)

    monkeypatch.chdir(other_root)
    result = service.save(snapshot)
    restarted = load_runtime_context(root=runtime_root)

    assert result.success is True
    assert (runtime_root / "config.local.json").exists()
    assert not (other_root / "config.local.json").exists()
    assert restarted.project_root == runtime_root.resolve()
    assert restarted.load_result.config["logging"]["retention_days"] == 72

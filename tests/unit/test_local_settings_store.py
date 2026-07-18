from dataclasses import replace
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.config.env_loader import load_environment
from safedesk.settings import LocalSettingsStore, managed_snapshot_from_config


def _store(tmp_path, replace_func=None):
    kwargs = {"root": tmp_path}
    if replace_func is not None:
        kwargs["replace_func"] = replace_func
    return LocalSettingsStore(load_environment(environ={}), **kwargs)


def test_valid_save_creates_local_file_preserves_unrelated_keys_and_zero_change_is_noop(tmp_path):
    example_path = tmp_path / "config.example.json"
    example_content = json.dumps({"app": {"name": "SafeDesk"}}, indent=2)
    example_path.write_text(example_content, encoding="utf-8")
    local_path = tmp_path / "config.local.json"
    local_path.write_text(
        json.dumps(
            {
                "alarm": {"audio_file": "preview.wav"},
                "owner_profile": {"owner_name": "Local Owner"},
            }
        ),
        encoding="utf-8",
    )
    snapshot = replace(managed_snapshot_from_config(DEFAULT_CONFIG), start_maximized=True)
    store = _store(tmp_path)

    result = store.save(snapshot)
    data = json.loads(local_path.read_text(encoding="utf-8"))

    assert result.success and result.restart_required
    assert result.changed_setting_count == 1
    assert data["owner_profile"]["owner_name"] == "Local Owner"
    assert data["alarm"]["audio_file"] == "preview.wav"
    assert data["ui"]["start_maximized"] is True
    assert "authentication" not in data
    assert example_path.read_text(encoding="utf-8") == example_content
    second = store.save(snapshot)
    assert second.success and second.changed_setting_count == 0
    assert second.restart_required is False


def test_malformed_or_non_object_local_json_is_not_overwritten(tmp_path):
    local_path = tmp_path / "config.local.json"
    snapshot = replace(managed_snapshot_from_config(DEFAULT_CONFIG), start_maximized=True)
    for content in ("{broken", "[]"):
        local_path.write_text(content, encoding="utf-8")
        result = _store(tmp_path).save(snapshot)
        assert result.success is False
        assert local_path.read_text(encoding="utf-8") == content


def test_invalid_candidate_does_not_modify_existing_file(tmp_path):
    local_path = tmp_path / "config.local.json"
    original = json.dumps({"alarm": {"enabled": True}})
    local_path.write_text(original, encoding="utf-8")
    snapshot = replace(managed_snapshot_from_config(DEFAULT_CONFIG), start_maximized=True)

    result = _store(tmp_path).save(snapshot)

    assert result.success is False
    assert local_path.read_text(encoding="utf-8") == original


def test_failed_atomic_replace_preserves_original_and_cleans_temporary_file(tmp_path):
    local_path = tmp_path / "config.local.json"
    original = json.dumps({"owner_profile": {"owner_name": "Preserved"}})
    local_path.write_text(original, encoding="utf-8")
    snapshot = replace(managed_snapshot_from_config(DEFAULT_CONFIG), start_maximized=True)

    def fail_replace(source, destination):
        raise OSError("simulated")

    result = _store(tmp_path, fail_replace).save(snapshot)

    assert result.success is False
    assert local_path.read_text(encoding="utf-8") == original
    assert not (tmp_path / "config.local.json.tmp").exists()
    assert str(tmp_path) not in result.message


def test_readback_verification_failure_does_not_claim_success(tmp_path):
    local_path = tmp_path / "config.local.json"
    snapshot = replace(managed_snapshot_from_config(DEFAULT_CONFIG), start_maximized=True)
    store = _store(tmp_path)
    store._verify_persisted_data = lambda _expected: False

    result = store.save(snapshot)

    assert result.success is False
    assert result.status == "verification_failed"
    assert "verified" not in result.message.lower()
    assert local_path.exists()


def test_restore_defaults_removes_only_managed_keys_and_preserves_runtime_data(tmp_path):
    local_path = tmp_path / "config.local.json"
    data_file = tmp_path / "data" / "intruders" / "evidence.jpg"
    data_file.parent.mkdir(parents=True)
    data_file.write_bytes(b"evidence")
    local_path.write_text(
        json.dumps(
            {
                "ui": {"start_maximized": True, "theme": "dark"},
                "alarm": {
                    "audio_file": "preview.wav",
                    "manual_preview_enabled": False,
                    "volume": 0.2,
                },
                "owner_profile": {"owner_name": "Preserved"},
            }
        ),
        encoding="utf-8",
    )

    result = _store(tmp_path).restore_defaults()
    restored = json.loads(local_path.read_text(encoding="utf-8"))

    assert result.success and result.restart_required
    assert "start_maximized" not in restored["ui"]
    assert restored["ui"]["theme"] == "dark"
    assert restored["alarm"] == {"audio_file": "preview.wav"}
    assert restored["owner_profile"]["owner_name"] == "Preserved"
    assert data_file.read_bytes() == b"evidence"
    assert local_path.exists()


def test_missing_local_file_and_restore_with_no_managed_keys_are_safe(tmp_path):
    store = _store(tmp_path)
    assert store.local_override_present() is False
    result = store.restore_defaults()
    assert result.success and result.changed_setting_count == 0
    assert not (tmp_path / "config.local.json").exists()

"""Configuration loading and merging for SafeDesk."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.config.exceptions import SafeDeskConfigFileError
from safedesk.config.models import ConfigLoadResult
from safedesk.storage.paths import config_example_path, local_config_path, project_root


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Return a recursive merge without mutating inputs."""

    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _load_json_file(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SafeDeskConfigFileError(f"Invalid JSON in {path.name}: {exc.msg}") from exc
    except OSError as exc:
        raise SafeDeskConfigFileError(f"Unable to read {path.name}: {exc}") from exc

    if not isinstance(data, dict):
        raise SafeDeskConfigFileError(f"{path.name} must contain a JSON object.")
    return data


def load_config(
    root: Path | None = None,
    example_path: Path | None = None,
    local_path: Path | None = None,
) -> ConfigLoadResult:
    """Load DEFAULT_CONFIG, public example config, and optional local config."""

    base_root = root or project_root()
    example = example_path or config_example_path(base_root)
    local = local_path or local_config_path(base_root)

    config = copy.deepcopy(DEFAULT_CONFIG)
    loaded_files: list[Path] = []
    local_config_loaded = False

    if example.exists():
        config = deep_merge(config, _load_json_file(example))
        loaded_files.append(example)

    if local.exists():
        config = deep_merge(config, _load_json_file(local))
        loaded_files.append(local)
        local_config_loaded = True

    return ConfigLoadResult(
        config=config,
        loaded_files=tuple(loaded_files),
        local_config_loaded=local_config_loaded,
    )

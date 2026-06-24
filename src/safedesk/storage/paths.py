"""Path helpers for SafeDesk configuration and runtime directories."""

from pathlib import Path

from safedesk.utils.constants import (
    CACHE_DATA_DIRNAME,
    CONFIG_DATA_DIRNAME,
    CONFIG_EXAMPLE_FILENAME,
    DATA_DIRNAME,
    ENV_FILENAME,
    INTRUDER_DATA_DIRNAME,
    LOCAL_CONFIG_FILENAME,
    LOGS_DATA_DIRNAME,
    OWNER_DATA_DIRNAME,
)


def project_root() -> Path:
    """Return the repository root based on the src package location."""

    return Path(__file__).resolve().parents[3]


def config_example_path(root: Path | None = None) -> Path:
    return (root or project_root()) / CONFIG_EXAMPLE_FILENAME


def local_config_path(root: Path | None = None) -> Path:
    return (root or project_root()) / LOCAL_CONFIG_FILENAME


def env_path(root: Path | None = None) -> Path:
    return (root or project_root()) / ENV_FILENAME


def data_dir(root: Path | None = None) -> Path:
    return (root or project_root()) / DATA_DIRNAME


def owner_data_dir(root: Path | None = None) -> Path:
    return data_dir(root) / OWNER_DATA_DIRNAME


def intruder_data_dir(root: Path | None = None) -> Path:
    return data_dir(root) / INTRUDER_DATA_DIRNAME


def logs_data_dir(root: Path | None = None) -> Path:
    return data_dir(root) / LOGS_DATA_DIRNAME


def cache_data_dir(root: Path | None = None) -> Path:
    return data_dir(root) / CACHE_DATA_DIRNAME


def config_data_dir(root: Path | None = None) -> Path:
    return data_dir(root) / CONFIG_DATA_DIRNAME


def runtime_data_dirs(root: Path | None = None) -> dict[str, Path]:
    """Return expected SafeDesk runtime directories without creating files."""

    return {
        "owner_data_dir": owner_data_dir(root),
        "intruder_data_dir": intruder_data_dir(root),
        "logs_dir": logs_data_dir(root),
        "cache_dir": cache_data_dir(root),
        "config_dir": config_data_dir(root),
    }

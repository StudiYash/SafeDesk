"""Lazy compute device detection for local recognition."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ComputeDeviceStatus:
    """TensorFlow compute device status for recognition."""

    available: bool
    device_type: str
    message: str
    gpu_names: tuple[str, ...] = ()


def detect_compute_device(
    import_module: Callable[[str], Any] = importlib.import_module,
) -> ComputeDeviceStatus:
    """Detect TensorFlow GPU visibility without forcing GPU usage."""

    try:
        tensorflow = import_module("tensorflow")
    except ModuleNotFoundError:
        return ComputeDeviceStatus(
            False,
            "unknown",
            "TensorFlow is not installed or could not be found. Install recognition requirements before checking compute devices.",
        )
    except Exception as exc:
        return ComputeDeviceStatus(False, "unknown", f"TensorFlow could not be imported. Details: {exc}")

    try:
        gpu_devices = tensorflow.config.list_physical_devices("GPU")
    except Exception as exc:
        return ComputeDeviceStatus(False, "unknown", f"TensorFlow imported, but compute devices could not be checked. Details: {exc}")

    if gpu_devices:
        gpu_names = tuple(str(getattr(device, "name", device)) for device in gpu_devices)
        return ComputeDeviceStatus(
            True,
            "gpu",
            "GPU device available for TensorFlow-backed recognition.",
            gpu_names,
        )

    return ComputeDeviceStatus(
        True,
        "cpu",
        "Running recognition in CPU mode. Verification may take longer.",
    )

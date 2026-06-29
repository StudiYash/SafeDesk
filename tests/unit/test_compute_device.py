from pathlib import Path
import importlib
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_compute_device_module_does_not_import_tensorflow_globally():
    tensorflow_was_loaded = "tensorflow" in sys.modules

    importlib.import_module("safedesk.vision.compute_device")

    assert ("tensorflow" in sys.modules) is tensorflow_was_loaded


def test_missing_tensorflow_returns_unknown_unavailable_status():
    compute_device = importlib.import_module("safedesk.vision.compute_device")

    def missing_import(_name):
        raise ModuleNotFoundError("tensorflow")

    status = compute_device.detect_compute_device(import_module=missing_import)

    assert status.available is False
    assert status.device_type == "unknown"
    assert "TensorFlow" in status.message


def test_tensorflow_without_gpu_returns_cpu_status():
    compute_device = importlib.import_module("safedesk.vision.compute_device")
    fake_tensorflow = SimpleNamespace(
        config=SimpleNamespace(list_physical_devices=lambda device_type: [] if device_type == "GPU" else [])
    )

    status = compute_device.detect_compute_device(import_module=lambda _name: fake_tensorflow)

    assert status.available is True
    assert status.device_type == "cpu"
    assert status.gpu_names == ()
    assert "CPU mode" in status.message


def test_tensorflow_with_gpu_returns_gpu_status():
    compute_device = importlib.import_module("safedesk.vision.compute_device")
    fake_gpu = SimpleNamespace(name="/physical_device:GPU:0")
    fake_tensorflow = SimpleNamespace(
        config=SimpleNamespace(list_physical_devices=lambda device_type: [fake_gpu] if device_type == "GPU" else [])
    )

    status = compute_device.detect_compute_device(import_module=lambda _name: fake_tensorflow)

    assert status.available is True
    assert status.device_type == "gpu"
    assert status.gpu_names == ("/physical_device:GPU:0",)
    assert "GPU device available" in status.message

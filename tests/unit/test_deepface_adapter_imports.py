from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import safedesk.vision.deepface_adapter as adapter


def test_deepface_adapter_imports_without_importing_deepface_globally():
    assert "deepface" not in sys.modules


def test_missing_deepface_dependency_returns_clean_status():
    def missing_import(_name):
        raise ModuleNotFoundError("deepface")

    status = adapter.check_deepface_dependency(import_module=missing_import)

    assert status.available is False
    assert "DeepFace is not installed" in status.message


def test_verify_faces_uses_injected_deepface_module():
    class FakeDeepFace:
        @staticmethod
        def verify(**_kwargs):
            return {"verified": True, "distance": 0.25}

        @staticmethod
        def represent(**_kwargs):
            return []

    def fake_import(_name):
        return SimpleNamespace(DeepFace=FakeDeepFace)

    result = adapter.verify_faces("a.jpg", "b.jpg", {"model_name": "ArcFace"}, import_module=fake_import)

    assert result.success is True
    assert result.verified is True
    assert result.distance == 0.25


def test_package_level_deepface_api_is_accepted():
    class FakeDeepFace:
        @staticmethod
        def verify(**_kwargs):
            return {"verified": False, "distance": 0.9}

        @staticmethod
        def represent(**_kwargs):
            return []

    def fake_import(name):
        assert name == "deepface"
        return SimpleNamespace(DeepFace=FakeDeepFace)

    status = adapter.check_deepface_dependency(import_module=fake_import)

    assert status.available is True


def test_deepface_submodule_fallback_is_accepted():
    class FakeDeepFaceModule:
        @staticmethod
        def verify(**_kwargs):
            return {"verified": True, "distance": 0.2}

        @staticmethod
        def represent(**_kwargs):
            return []

    def fake_import(name):
        if name == "deepface":
            return SimpleNamespace()
        if name == "deepface.DeepFace":
            return FakeDeepFaceModule
        raise AssertionError(name)

    status = adapter.check_deepface_dependency(import_module=fake_import)

    assert status.available is True


def test_deepface_missing_expected_api_returns_unavailable():
    def fake_import(_name):
        return SimpleNamespace(DeepFace=SimpleNamespace(verify=lambda **_kwargs: None))

    status = adapter.check_deepface_dependency(import_module=fake_import)

    assert status.available is False
    assert "verify/represent" in status.message


def test_deepface_import_exception_returns_clean_message():
    def broken_import(_name):
        raise RuntimeError("broken")

    status = adapter.check_deepface_dependency(import_module=broken_import)

    assert status.available is False
    assert "could not be imported" in status.message

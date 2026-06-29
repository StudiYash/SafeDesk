"""Lazy DeepFace adapter for local demo recognition."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class DeepFaceDependencyStatus:
    available: bool
    message: str


@dataclass(frozen=True)
class DeepFaceEmbeddingResult:
    success: bool
    message: str
    representation_count: int = 0


@dataclass(frozen=True)
class DeepFaceVerifyResult:
    success: bool
    message: str
    verified: bool = False
    distance: float | None = None


def _load_deepface(import_module: Callable[[str], Any] = importlib.import_module) -> tuple[Any | None, str | None]:
    try:
        package = import_module("deepface")
    except ModuleNotFoundError:
        return None, "DeepFace is not installed. Run `python -m pip install -r requirements.txt` before using recognition."
    except Exception as exc:
        return None, f"DeepFace could not be imported. Details: {exc}"

    candidate = getattr(package, "DeepFace", None)
    if candidate is None:
        try:
            candidate = import_module("deepface.DeepFace")
        except Exception as exc:
            return None, f"DeepFace is installed but its API could not be loaded. Details: {exc}"

    if not callable(getattr(candidate, "verify", None)) or not callable(getattr(candidate, "represent", None)):
        return None, "DeepFace is installed, but the expected verify/represent API was not found."

    return candidate, None


def check_deepface_dependency(
    import_module: Callable[[str], Any] = importlib.import_module,
) -> DeepFaceDependencyStatus:
    deepface, error = _load_deepface(import_module)
    if deepface is None:
        return DeepFaceDependencyStatus(False, error or "DeepFace is not available.")
    return DeepFaceDependencyStatus(True, "DeepFace is importable. Model files may still need first-run setup.")


def compute_face_representation(
    image: str | Path | Any,
    recognition_config: dict[str, Any],
    import_module: Callable[[str], Any] = importlib.import_module,
) -> DeepFaceEmbeddingResult:
    deepface, error = _load_deepface(import_module)
    if deepface is None:
        return DeepFaceEmbeddingResult(False, error or "DeepFace is not available.")

    try:
        representations = deepface.represent(
            img_path=str(image) if isinstance(image, Path) else image,
            model_name=recognition_config.get("model_name", "ArcFace"),
            detector_backend=recognition_config.get("detector_backend", "retinaface"),
            enforce_detection=bool(recognition_config.get("enforce_detection", True)),
            align=bool(recognition_config.get("align", True)),
        )
    except Exception as exc:
        return DeepFaceEmbeddingResult(
            False,
            "DeepFace could not compute a face representation. First-run model setup may need internet, or no clear face was detected."
            f" Details: {exc}",
        )

    count = len(representations) if isinstance(representations, list) else 1
    return DeepFaceEmbeddingResult(True, "Face representation computed locally.", representation_count=count)


def verify_faces(
    image_a: str | Path | Any,
    image_b: str | Path | Any,
    recognition_config: dict[str, Any],
    import_module: Callable[[str], Any] = importlib.import_module,
) -> DeepFaceVerifyResult:
    deepface, error = _load_deepface(import_module)
    if deepface is None:
        return DeepFaceVerifyResult(False, error or "DeepFace is not available.")

    try:
        result = deepface.verify(
            img1_path=str(image_a) if isinstance(image_a, Path) else image_a,
            img2_path=str(image_b) if isinstance(image_b, Path) else image_b,
            model_name=recognition_config.get("model_name", "ArcFace"),
            detector_backend=recognition_config.get("detector_backend", "retinaface"),
            distance_metric=recognition_config.get("distance_metric", "cosine"),
            enforce_detection=bool(recognition_config.get("enforce_detection", True)),
            align=bool(recognition_config.get("align", True)),
        )
    except Exception as exc:
        return DeepFaceVerifyResult(
            False,
            "DeepFace could not verify the faces. First-run model setup may need internet, or one image may not contain a clear detectable face."
            f" Details: {exc}",
        )

    distance = result.get("distance") if isinstance(result, dict) else None
    return DeepFaceVerifyResult(
        True,
        "Face verification completed locally.",
        verified=bool(result.get("verified", False)) if isinstance(result, dict) else False,
        distance=float(distance) if distance is not None else None,
    )

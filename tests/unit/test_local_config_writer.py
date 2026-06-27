from pathlib import Path
import sys

import json
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.exceptions import SafeDeskValidationError
from safedesk.config.local_config_writer import (
    LocalSetupPayload,
    build_safe_local_config,
    save_local_setup_config,
)


def _payload():
    return LocalSetupPayload(
        owner_name="Local Owner",
        owner_email="owner@example.com",
        preferred_security_mode="demo_safe",
        demo_safe_mode=True,
        camera_index=0,
        privacy_acknowledged=True,
        safe_mode_acknowledged=True,
    )


def test_local_config_writer_writes_only_safe_allowed_fields(tmp_path):
    path = tmp_path / "config.local.json"

    save_local_setup_config(_payload(), path=path)
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["setup"]["completed"] is True
    assert data["owner_profile"]["owner_name"] == "Local Owner"
    assert data["security_mode"]["default_mode"] == "demo_safe"
    assert data["setup_preferences"]["camera_index"] == 0

    serialized = json.dumps(data).lower()
    for forbidden in ("password", "otp_secret", "panic_code", "token", "face_image", "face_encoding"):
        assert forbidden not in serialized


def test_local_config_writer_preserves_existing_safe_values():
    existing = {
        "ui": {"theme": "light"},
        "setup_preferences": {"existing_safe_note": "keep"},
    }

    data = build_safe_local_config(_payload(), existing=existing)

    assert data["ui"]["theme"] == "light"
    assert data["setup_preferences"]["existing_safe_note"] == "keep"
    assert data["setup_preferences"]["privacy_acknowledged"] is True


def test_local_config_writer_rejects_sensitive_existing_fields():
    with pytest.raises(SafeDeskValidationError):
        build_safe_local_config(_payload(), existing={"auth": {"password_hash": "bad"}})


def test_local_config_writer_rejects_invalid_payload(tmp_path):
    bad_payload = LocalSetupPayload(
        owner_name="",
        privacy_acknowledged=True,
        safe_mode_acknowledged=True,
    )

    with pytest.raises(SafeDeskValidationError):
        save_local_setup_config(bad_payload, path=tmp_path / "config.local.json")

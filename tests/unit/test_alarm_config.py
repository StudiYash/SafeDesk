from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.config.env_loader import load_environment
from safedesk.config.validators import validate_config


def _report_for(overrides):
    config = deep_merge(DEFAULT_CONFIG, {"alarm": overrides})
    return validate_config(config, load_environment(environ={}), root=ROOT)


def test_default_alarm_config_is_complete_and_valid():
    report = validate_config(DEFAULT_CONFIG, load_environment(environ={}), root=ROOT)
    example = json.loads((ROOT / "config.example.json").read_text(encoding="utf-8"))
    expected = {
        "enabled",
        "foundation_enabled",
        "demo_only",
        "manual_preview_enabled",
        "automatic_trigger_enabled",
        "allow_looping",
        "max_preview_duration_seconds",
        "beep_fallback_enabled",
        "audio_file",
        "allowed_audio_dir",
        "volume",
    }

    assert report.is_valid is True
    assert set(DEFAULT_CONFIG["alarm"]) == expected
    assert set(example["alarm"]) == expected


def test_alarm_section_and_boolean_fields_are_validated():
    config = deep_merge(DEFAULT_CONFIG, {"alarm": "preview"})
    section_report = validate_config(config, load_environment(environ={}), root=ROOT)
    boolean_report = _report_for(
        {
            "enabled": 0,
            "foundation_enabled": "yes",
            "demo_only": 1,
            "manual_preview_enabled": "yes",
            "automatic_trigger_enabled": 0,
            "allow_looping": 0,
            "beep_fallback_enabled": "yes",
        }
    )

    assert "invalid_alarm_section" in {issue.code for issue in section_report.errors}
    assert "invalid_alarm_boolean" in {issue.code for issue in boolean_report.errors}


def test_phase24_alarm_safety_flags_are_enforced():
    assert "alarm_real_enablement_disabled" in {issue.code for issue in _report_for({"enabled": True}).errors}
    assert "alarm_demo_only_required" in {issue.code for issue in _report_for({"demo_only": False}).errors}
    assert "alarm_automatic_trigger_disabled" in {
        issue.code for issue in _report_for({"automatic_trigger_enabled": True}).errors
    }
    assert "alarm_looping_disabled" in {issue.code for issue in _report_for({"allow_looping": True}).errors}


def test_alarm_duration_and_volume_ranges_reject_booleans():
    for value in (0, 11, True):
        assert "invalid_alarm_preview_duration" in {
            issue.code for issue in _report_for({"max_preview_duration_seconds": value}).errors
        }
    for value in (-0.1, 1.1, True):
        assert "invalid_number_range" in {issue.code for issue in _report_for({"volume": value}).errors}


def test_alarm_audio_file_validation_accepts_only_safe_relative_wav_paths():
    assert _report_for({"audio_file": ""}).is_valid is True
    assert _report_for({"audio_file": "preview.wav"}).is_valid is True
    assert _report_for({"audio_file": "assets/audio/preview.wav"}).is_valid is True
    assert "unsafe_alarm_audio_file" in {issue.code for issue in _report_for({"audio_file": "../preview.wav"}).errors}
    assert "unsafe_alarm_audio_file" in {
        issue.code for issue in _report_for({"audio_file": r"C:\Users\owner\preview.wav"}).errors
    }
    assert "unsafe_alarm_audio_file" in {issue.code for issue in _report_for({"audio_file": "/tmp/preview.wav"}).errors}
    assert "unsupported_alarm_audio_file" in {issue.code for issue in _report_for({"audio_file": "preview.mp3"}).errors}


def test_alarm_allowed_audio_directory_must_be_safe_and_relative():
    assert "invalid_alarm_audio_directory" in {issue.code for issue in _report_for({"allowed_audio_dir": ""}).errors}
    assert "unsafe_alarm_audio_directory" in {issue.code for issue in _report_for({"allowed_audio_dir": "."}).errors}
    assert "unsafe_alarm_audio_directory" in {
        issue.code for issue in _report_for({"allowed_audio_dir": "../audio"}).errors
    }
    assert "unsafe_alarm_audio_directory" in {
        issue.code for issue in _report_for({"allowed_audio_dir": r"C:\audio"}).errors
    }

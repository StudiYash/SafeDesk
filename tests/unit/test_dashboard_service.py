from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.dashboard import DashboardService
from safedesk.logging.log_models import SafeDeskEvent
from safedesk.logging.sqlite_log_store import SQLiteLogStore


def _config_for_tmp(root: Path):
    return deep_merge(
        DEFAULT_CONFIG,
        {
            "logging": {"database_path": "data/logs/safedesk.sqlite3"},
            "owner_face_registration": {
                "samples_dir": "data/owner/samples",
                "manifest_path": "data/config/owner_registration_manifest.json",
            },
            "intruder_detection": {
                "manifest_path": "data/config/intruder_capture_manifest.json",
                "intruder_images_dir": "data/intruders",
            },
        },
    )


def _all_dashboard_values(summary) -> list[str]:
    values: list[str] = []
    for section in summary.sections:
        values.append(section.title)
        for row in section.rows:
            values.extend((row.label, row.value))
    for event in summary.recent_events:
        values.extend((event.timestamp, event.category, event.action, event.status, event.severity, event.message))
    return values


def test_dashboard_service_builds_default_summary_without_local_files(tmp_path):
    summary = DashboardService(_config_for_tmp(tmp_path), tmp_path).build_summary()
    section_titles = {section.title for section in summary.sections}

    assert "SafeDesk Status" in section_titles
    assert "Owner Readiness" in section_titles
    assert "Lockdown Readiness" in section_titles
    assert "Intruder Evidence" in section_titles
    assert summary.recent_events == ()
    assert summary.intruder_history.total_count == 0


def test_dashboard_service_reports_setup_profile_and_lockdown_status_safely(tmp_path):
    config = deep_merge(
        _config_for_tmp(tmp_path),
        {
            "owner_profile": {"owner_name": "Owner", "owner_email": "owner@example.test"},
            "setup": {"completed": True},
        },
    )

    summary = DashboardService(config, tmp_path).build_summary()
    values = _all_dashboard_values(summary)

    assert "yes" in values
    assert "enabled (ctrl+alt+l)" in values
    assert str(tmp_path) not in "\n".join(values)


def test_dashboard_service_handles_missing_state_files_gracefully(tmp_path):
    summary = DashboardService(_config_for_tmp(tmp_path), tmp_path).build_summary()
    threat_section = next(section for section in summary.sections if section.title == "Threat & Protection")
    state_rows = {row.label: row.value for row in threat_section.rows}

    assert state_rows["Threat state"] == "No local state yet"
    assert state_rows["Protected mode"] == "No local state yet"
    assert state_rows["Shutdown escalation"] == "No local state yet"


def test_dashboard_service_reports_safe_alarm_readiness_without_audio_details(tmp_path):
    summary = DashboardService(_config_for_tmp(tmp_path), tmp_path).build_summary()
    threat_section = next(section for section in summary.sections if section.title == "Threat & Protection")
    rows = {row.label: row.value for row in threat_section.rows}

    assert rows["Alarm foundation"] == "enabled"
    assert rows["Manual alarm preview"] == "enabled"
    assert rows["Automatic alarm trigger"] == "disabled"
    assert rows["Alarm looping"] == "disabled"
    assert "audio" not in "\n".join(rows)
    assert ".wav" not in "\n".join(rows.values())


def test_dashboard_service_reads_recent_events_without_metadata_dump(tmp_path):
    config = _config_for_tmp(tmp_path)
    store = SQLiteLogStore(tmp_path / "data" / "logs" / "safedesk.sqlite3")
    store.add_event(
        SafeDeskEvent(
            category="app",
            action="dashboard_test",
            status="info",
            severity="INFO",
            message="Safe dashboard test event.",
            metadata={"private": "not shown"},
        )
    )

    summary = DashboardService(config, tmp_path).build_summary()

    assert len(summary.recent_events) == 1
    assert summary.recent_events[0].action == "dashboard_test"
    assert "private" not in "\n".join(_all_dashboard_values(summary))


def test_dashboard_service_hides_windows_paths_in_recent_event_messages(tmp_path):
    config = _config_for_tmp(tmp_path)
    store = SQLiteLogStore(tmp_path / "data" / "logs" / "safedesk.sqlite3")
    store.add_event(
        SafeDeskEvent(
            category="app",
            action="dashboard_path_test",
            status="info",
            severity="INFO",
            message=r"Preview stored at C:\Users\owner\SafeDesk\data\intruders\capture.jpg",
            metadata={},
        )
    )

    summary = DashboardService(config, tmp_path).build_summary()
    message = summary.recent_events[0].message

    assert "[local path hidden]" in message
    assert "C:" not in message
    assert "Users" not in message
    assert "capture.jpg" not in message


def test_dashboard_service_hides_project_data_paths_in_recent_event_messages(tmp_path):
    config = _config_for_tmp(tmp_path)
    store = SQLiteLogStore(tmp_path / "data" / "logs" / "safedesk.sqlite3")
    store.add_event(
        SafeDeskEvent(
            category="app",
            action="dashboard_data_path_test",
            status="info",
            severity="INFO",
            message="Manual evidence saved at data/intruders/capture.jpg",
            metadata={},
        )
    )

    summary = DashboardService(config, tmp_path).build_summary()
    message = summary.recent_events[0].message

    assert "[local path hidden]" in message
    assert "data/intruders" not in message
    assert "capture.jpg" not in message


def test_dashboard_service_does_not_expose_sensitive_terms_or_full_paths(tmp_path):
    summary = DashboardService(_config_for_tmp(tmp_path), tmp_path).build_summary()
    joined = "\n".join(_all_dashboard_values(summary)).lower()

    assert str(tmp_path).lower() not in joined
    for forbidden in ("password", "recovery code", "panic code", "hash", "salt", "secret"):
        assert forbidden not in joined

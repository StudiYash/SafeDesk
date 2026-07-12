"""Safe owner/admin dashboard summary service."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from safedesk.dashboard.dashboard_models import (
    DashboardEventSummary,
    DashboardRow,
    DashboardSection,
    DashboardSummary,
)
from safedesk.intruder_history import IntruderHistoryReader
from safedesk.logging.dashboard_helpers import format_event_timestamp_for_display
from safedesk.logging.sqlite_log_store import SQLiteLogStore
from safedesk.protected_mode.protected_state import load_protected_mode_state
from safedesk.shutdown_escalation.shutdown_state import load_shutdown_state
from safedesk.storage.paths import project_root
from safedesk.threats.threat_state import load_threat_state
from safedesk.vision.owner_manifest import build_registration_status

LOCAL_PATH_PLACEHOLDER = "[local path hidden]"
WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r"(?i)\b[a-z]:[\\/][^\s,;|<>\"']+")
HOME_PATH_PATTERN = re.compile(r"(?i)(?<![\w.-])(?:~[\\/][^\s,;|<>\"']+|[\\/](?:Users|home)[\\/][^\s,;|<>\"']+)")
PROJECT_DATA_PATH_PATTERN = re.compile(
    r"(?i)(?<![\w.-])data[\\/](?:intruders|config|owner|logs|cache)(?:[\\/][^\s,;|<>\"']*)?"
)


class DashboardService:
    """Build owner-only SafeDesk status summaries without exposing private paths."""

    def __init__(self, config: dict, root: Path | None = None):
        self.config = config
        self.root = root or project_root()

    def build_summary(self, recent_event_limit: int = 5) -> DashboardSummary:
        intruder_history = IntruderHistoryReader(self.config, self.root).build_summary()
        recent_events = self._recent_events(limit=recent_event_limit)
        sections = (
            self._safedesk_status_section(),
            self._owner_readiness_section(),
            self._face_liveness_section(),
            self._lockdown_readiness_section(),
            self._threat_protection_section(),
            self._event_logging_section(len(recent_events)),
            self._intruder_evidence_section(intruder_history),
        )
        return DashboardSummary(sections=sections, recent_events=recent_events, intruder_history=intruder_history)

    def _safedesk_status_section(self) -> DashboardSection:
        app = self.config.get("app", {})
        return DashboardSection(
            "SafeDesk Status",
            rows=(
                DashboardRow("Application", self._safe_text(app.get("name", "SafeDesk"))),
                DashboardRow("Version", self._safe_text(app.get("version", "unknown"))),
                DashboardRow("Environment", self._safe_text(app.get("environment", "development"))),
                DashboardRow("Demo/safe mode", self._yes_no(app.get("demo_safe_mode", True))),
                DashboardRow("Security mode", self._safe_text(self.config.get("security_mode", {}).get("default_mode", "unknown"))),
            ),
        )

    def _owner_readiness_section(self) -> DashboardSection:
        owner = self.config.get("owner_profile", {})
        setup = self.config.get("setup", {})
        owner_name = str(owner.get("owner_name", "")).strip()
        owner_contact = str(owner.get("owner_email", "")).strip()
        return DashboardSection(
            "Owner Readiness",
            rows=(
                DashboardRow("Owner profile configured", self._yes_no(bool(owner_name))),
                DashboardRow("Owner email configured", self._yes_no(bool(owner_contact))),
                DashboardRow("Setup completed", self._yes_no(setup.get("completed", False))),
            ),
        )

    def _face_liveness_section(self) -> DashboardSection:
        owner_registration = self.config.get("owner_face_registration", {})
        recognition = self.config.get("owner_recognition", {})
        liveness = self.config.get("liveness", {})
        required_samples = int(owner_registration.get("required_samples", 5))
        status = build_registration_status(
            self._resolve_path(owner_registration.get("samples_dir", "data/owner/samples")),
            self._resolve_path(owner_registration.get("manifest_path", "data/config/owner_registration_manifest.json")),
            required_samples,
        )
        return DashboardSection(
            "Face & Liveness Readiness",
            rows=(
                DashboardRow("Owner samples", f"{status.sample_count} / {status.required_sample_count}"),
                DashboardRow("Owner registration complete", self._yes_no(status.registration_complete)),
                DashboardRow("Recognition foundation", self._enabled_disabled(recognition.get("enabled", True))),
                DashboardRow("Liveness foundation", self._enabled_disabled(liveness.get("enabled", True))),
            ),
        )

    def _lockdown_readiness_section(self) -> DashboardSection:
        background = self.config.get("background_agent", {})
        shortcut = self.config.get("global_shortcut", {})
        display = self.config.get("lockdown_display", {})
        interaction = self.config.get("safe_interaction_lock", {})
        return DashboardSection(
            "Lockdown Readiness",
            rows=(
                DashboardRow("Background agent", self._foundation_state(background)),
                DashboardRow("Tray", self._enabled_disabled(background.get("system_tray_enabled", False))),
                DashboardRow("Global shortcut", self._shortcut_status(shortcut)),
                DashboardRow("Lockdown display", self._foundation_state(display)),
                DashboardRow("Safe interaction lock", self._foundation_state(interaction)),
            ),
        )

    def _threat_protection_section(self) -> DashboardSection:
        threat_config = self.config.get("threat_levels", {})
        protected_config = self.config.get("protected_mode", {})
        shutdown_config = self.config.get("shutdown", {})
        alarm_config = self.config.get("alarm", {})

        threat_path = self._resolve_path(threat_config.get("state_path", "data/config/threat_state.json"))
        protected_path = self._resolve_path(protected_config.get("state_path", "data/config/protected_mode_state.json"))
        shutdown_path = self._resolve_path(shutdown_config.get("state_path", "data/config/shutdown_state.json"))

        threat_value = "No local state yet"
        if threat_path.exists():
            threat_state = load_threat_state(
                threat_path,
                int(threat_config.get("initial_level", 0)),
                bool(threat_config.get("demo_only", True)),
            )
            threat_value = f"Level {threat_state.current_level} / highest {threat_state.highest_level}"

        protected_value = "No local state yet"
        if protected_path.exists():
            protected_state = load_protected_mode_state(protected_path, bool(protected_config.get("demo_only", True)))
            protected_value = f"{protected_state.mode} | armed: {self._yes_no(protected_state.armed)}"

        shutdown_value = "No local state yet"
        if shutdown_path.exists():
            shutdown_state = load_shutdown_state(
                shutdown_path,
                bool(shutdown_config.get("demo_shutdown_only", True)),
                bool(shutdown_config.get("require_manual_confirmation", True)),
            )
            shutdown_value = f"{shutdown_state.mode} | countdown: {self._yes_no(shutdown_state.countdown_running)}"

        return DashboardSection(
            "Threat & Protection",
            rows=(
                DashboardRow("Threat state", threat_value),
                DashboardRow("Protected mode", protected_value),
                DashboardRow("Shutdown escalation", shutdown_value),
                DashboardRow("Alarm foundation", self._enabled_disabled(alarm_config.get("foundation_enabled", True))),
                DashboardRow("Manual alarm preview", self._enabled_disabled(alarm_config.get("manual_preview_enabled", True))),
                DashboardRow("Automatic alarm trigger", self._enabled_disabled(alarm_config.get("automatic_trigger_enabled", False))),
                DashboardRow("Alarm looping", self._enabled_disabled(alarm_config.get("allow_looping", False))),
            ),
        )

    def _event_logging_section(self, recent_count: int) -> DashboardSection:
        logging_config = self.config.get("logging", {})
        store = SQLiteLogStore(self._resolve_path(logging_config.get("database_path", "data/logs/safedesk.sqlite3")))
        status = store.build_status(enabled=logging_config.get("enabled", True))
        return DashboardSection(
            "Event Logging",
            rows=(
                DashboardRow("Logging", self._enabled_disabled(status.enabled)),
                DashboardRow("Database", "ready" if status.database_ready else "not created yet"),
                DashboardRow("Stored events", str(status.event_count)),
                DashboardRow("Recent summaries", str(recent_count)),
            ),
        )

    def _intruder_evidence_section(self, intruder_history) -> DashboardSection:
        return DashboardSection(
            "Intruder Evidence",
            rows=(
                DashboardRow("Evidence count", str(intruder_history.total_count)),
                DashboardRow("Images available", str(intruder_history.image_available_count)),
                DashboardRow("Most recent capture", intruder_history.most_recent_capture),
                DashboardRow("Review", "Open Intruder History from the Admin Console sidebar."),
            ),
        )

    def _recent_events(self, limit: int) -> tuple[DashboardEventSummary, ...]:
        logging_config = self.config.get("logging", {})
        store = SQLiteLogStore(self._resolve_path(logging_config.get("database_path", "data/logs/safedesk.sqlite3")))
        try:
            events = store.list_recent_events(limit)
        except Exception:
            events = []
        return tuple(
            DashboardEventSummary(
                event_number=event.event_number,
                timestamp=format_event_timestamp_for_display(event.timestamp),
                category=self._safe_text(event.category),
                action=self._safe_text(event.action),
                status=self._safe_text(event.status),
                severity=self._safe_text(event.severity),
                message=self._safe_text(event.message or "No message", limit=160),
            )
            for event in events
        )

    def _resolve_path(self, value: Any) -> Path:
        path = Path(str(value))
        return path if path.is_absolute() else self.root / path

    @staticmethod
    def _yes_no(value: Any) -> str:
        return "yes" if value is True or bool(value) else "no"

    @staticmethod
    def _enabled_disabled(value: Any) -> str:
        return "enabled" if value is True else "disabled"

    def _foundation_state(self, section: dict) -> str:
        if not isinstance(section, dict):
            return "not configured"
        if section.get("enabled", True) is not True:
            return "disabled"
        if section.get("foundation_enabled", True) is not True:
            return "foundation unavailable"
        return "enabled"

    def _shortcut_status(self, shortcut: dict) -> str:
        if not isinstance(shortcut, dict) or shortcut.get("enabled", True) is not True:
            return "disabled"
        hotkey = self._safe_text(shortcut.get("hotkey", "ctrl+alt+l"), limit=40)
        return f"enabled ({hotkey})"

    @staticmethod
    def _safe_text(value: Any, limit: int = 120) -> str:
        text = str(value or "").replace("\n", " ").replace("\r", " ").strip()
        text = DashboardService._hide_local_paths(text)
        return text[:limit] if text else "unknown"

    @staticmethod
    def _hide_local_paths(text: str) -> str:
        for pattern in (WINDOWS_ABSOLUTE_PATH_PATTERN, HOME_PATH_PATTERN, PROJECT_DATA_PATH_PATTERN):
            text = pattern.sub(LOCAL_PATH_PLACEHOLDER, text)
        return text

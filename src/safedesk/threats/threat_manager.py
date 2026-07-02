"""Deterministic demo-only threat scoring foundation."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from safedesk.logging.event_logger import EventLogger, build_logger_from_config
from safedesk.threats.threat_models import THREAT_EVENT_TYPES, ThreatAssessmentResult, ThreatState
from safedesk.threats.threat_state import default_threat_state, load_threat_state, resolve_threat_state_path, save_threat_state, utc_timestamp


class ThreatManager:
    """Local threat state manager for manual foundation simulations only."""

    def __init__(
        self,
        config: dict,
        state_path: Path | None = None,
        event_logger: EventLogger | None = None,
    ):
        self.config = config
        self.threat_config = config.get("threat_levels", {})
        self.state_path = state_path or resolve_threat_state_path(config)
        self.event_logger = event_logger or build_logger_from_config(config)

    @property
    def foundation_enabled(self) -> bool:
        return self.threat_config.get("foundation_enabled", True) is True

    @property
    def demo_only(self) -> bool:
        return self.threat_config.get("demo_only", True) is True

    @property
    def initial_level(self) -> int:
        return int(self.threat_config.get("initial_level", 0))

    @property
    def max_level(self) -> int:
        return int(self.threat_config.get("max_level", 5))

    def load_state(self) -> ThreatState:
        return load_threat_state(self.state_path, self.initial_level, self.demo_only)

    def save_state(self, state: ThreatState) -> None:
        save_threat_state(self.state_path, state)

    def record_event(self, event_type: str) -> ThreatAssessmentResult:
        """Apply one manual simulation event to local state."""

        state = self.load_state()
        previous_level = state.current_level

        if not self.foundation_enabled:
            return self._result(False, "blocked", previous_level, state, "Threat foundation is disabled in configuration.")

        if event_type not in THREAT_EVENT_TYPES or event_type == "manual_reset":
            return self._result(False, "invalid_event", previous_level, state, "Threat foundation received an unsupported manual event.")

        next_state, reason = self._apply_event(state, event_type)
        next_state = replace(
            next_state,
            current_level=max(0, min(self.max_level, next_state.current_level)),
            highest_level=max(state.highest_level, next_state.current_level),
            updated_at=utc_timestamp(),
            demo_only=True,
            last_reason=reason,
        )
        self.save_state(next_state)
        status = "updated" if next_state.current_level != previous_level else "unchanged"
        result = self._result(True, status, previous_level, next_state, reason)
        self._log_threat_event(event_type, result)
        if next_state.current_level != previous_level:
            self._log_level_change(result)
        if next_state.current_level >= 5:
            self._log_shutdown_candidate(result)
        return result

    def reset_state(self) -> ThreatAssessmentResult:
        """Reset ignored local threat state to Level 0."""

        previous = self.load_state()
        state = default_threat_state(0, True)
        state = replace(state, last_reason="Manual reset to safe idle.", updated_at=utc_timestamp())
        self.save_state(state)
        result = self._result(True, "reset", previous.current_level, state, "Threat state reset to safe idle.")
        self._log_reset(result)
        return result

    def _apply_event(self, state: ThreatState, event_type: str) -> tuple[ThreatState, str]:
        repeated_unknown_threshold = self._positive_config("repeated_unknown_threshold", 3)
        failed_password_threshold = self._positive_config("failed_password_threshold", 3)
        failed_otp_threshold = self._positive_config("failed_otp_threshold", 3)
        forceful_threshold = self._positive_config("forceful_attempt_threshold", 3)
        forced_exit_threshold = self._positive_config("forced_exit_threshold", 1)

        new_level = state.current_level
        unknown_count = state.unknown_unverified_count
        password_count = state.failed_password_count
        otp_count = state.failed_otp_count
        panic_count = state.failed_panic_count
        forced_exit_count = state.forced_exit_count

        if event_type == "unknown_unverified_face":
            unknown_count += 1
            new_level = max(new_level, 2 if unknown_count >= repeated_unknown_threshold else 1)
            reason = "Unknown/unverified face activity simulated."
        elif event_type == "repeated_unknown_unverified_face":
            unknown_count = max(unknown_count + 1, repeated_unknown_threshold)
            new_level = max(new_level, 2)
            reason = "Repeated unknown/unverified face activity simulated."
        elif event_type == "failed_password_attempt":
            password_count += 1
            new_level = max(new_level, 3 if password_count >= failed_password_threshold else new_level)
            reason = "Failed master-password attempt simulated."
        elif event_type == "failed_otp_attempt":
            otp_count += 1
            new_level = max(new_level, 3 if otp_count >= failed_otp_threshold else new_level)
            reason = "Failed OTP attempt simulated."
        elif event_type == "failed_panic_attempt":
            panic_count += 1
            new_level = max(new_level, 3 if panic_count >= failed_password_threshold else new_level)
            reason = "Failed panic/recovery-code attempt simulated."
        elif event_type == "forced_exit_attempt":
            forced_exit_count += 1
            new_level = max(new_level, 5 if forced_exit_count > forced_exit_threshold else 4)
            reason = "Forced-exit style attempt simulated."
        elif event_type == "serious_follow_up_event":
            new_level = max(new_level, 5 if new_level >= 4 else 1)
            reason = "Serious follow-up event simulated."
        else:
            reason = "Manual threat foundation test event recorded."

        combined_auth_failures = password_count + otp_count + panic_count
        active_auth_failure_types = sum(1 for count in (password_count, otp_count, panic_count) if count > 0)
        if active_auth_failure_types >= 2 and combined_auth_failures >= forceful_threshold:
            new_level = max(new_level, 4)
            reason = "Combined failed authentication simulations reached the forceful-access candidate threshold."

        return (
            ThreatState(
                current_level=new_level,
                highest_level=max(state.highest_level, new_level),
                unknown_unverified_count=unknown_count,
                failed_password_count=password_count,
                failed_otp_count=otp_count,
                failed_panic_count=panic_count,
                forced_exit_count=forced_exit_count,
                last_reason=reason,
                updated_at=state.updated_at,
                demo_only=True,
            ),
            reason,
        )

    def _positive_config(self, key: str, default: int) -> int:
        value = self.threat_config.get(key, default)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            return default
        return value

    @staticmethod
    def _result(success: bool, status: str, previous_level: int, state: ThreatState, reason: str) -> ThreatAssessmentResult:
        if state.current_level >= 5:
            message = "Shutdown escalation candidate reached in demo mode. No shutdown was performed."
        elif status == "reset":
            message = "Threat state reset to safe idle."
        elif success:
            message = f"Threat foundation state is now Level {state.current_level}."
        else:
            message = reason
        return ThreatAssessmentResult(
            success=success,
            status=status,
            previous_level=previous_level,
            new_level=state.current_level,
            highest_level=state.highest_level,
            reason=reason,
            message=message,
            state=state,
        )

    def _log_threat_event(self, event_type: str, result: ThreatAssessmentResult) -> None:
        severity = "WARNING" if result.new_level >= 4 else "INFO"
        self._safe_log(
            action="threat_event_recorded",
            status="success" if result.success else "skipped",
            severity=severity,
            message=f"Threat foundation event recorded: {event_type}.",
            result=result,
            event_type=event_type,
        )

    def _log_level_change(self, result: ThreatAssessmentResult) -> None:
        severity = "WARNING" if result.new_level >= 4 else "INFO"
        self._safe_log(
            action="threat_level_changed",
            status="success",
            severity=severity,
            message=f"Threat level changed from {result.previous_level} to {result.new_level}.",
            result=result,
        )

    def _log_shutdown_candidate(self, result: ThreatAssessmentResult) -> None:
        self._safe_log(
            action="shutdown_escalation_candidate",
            status="info",
            severity="WARNING",
            message="Shutdown escalation candidate reached in demo mode. No shutdown was performed.",
            result=result,
        )

    def _log_reset(self, result: ThreatAssessmentResult) -> None:
        self._safe_log(
            action="threat_state_reset",
            status="success",
            severity="INFO",
            message="Threat state reset to safe idle.",
            result=result,
            event_type="manual_reset",
        )

    def _safe_log(
        self,
        action: str,
        status: str,
        severity: str,
        message: str,
        result: ThreatAssessmentResult,
        event_type: str = "",
    ) -> None:
        try:
            metadata = {
                "event_type": event_type,
                "previous_level": result.previous_level,
                "new_level": result.new_level,
                "highest_level": result.highest_level,
                "unknown_unverified_count": result.state.unknown_unverified_count,
                "failed_password_count": result.state.failed_password_count,
                "failed_otp_count": result.state.failed_otp_count,
                "failed_panic_count": result.state.failed_panic_count,
                "forced_exit_count": result.state.forced_exit_count,
                "demo_only": True,
                "shutdown_performed": False,
                "protected_mode_active": False,
            }
            self.event_logger.log_event(
                category="threat_level",
                action=action,
                status=status,
                severity=severity,
                message=message,
                metadata=metadata,
            )
        except Exception:
            pass


def build_threat_manager_from_config(config: dict, state_path: Path | None = None) -> ThreatManager:
    """Build a threat manager from runtime config."""

    return ThreatManager(config, state_path=state_path)

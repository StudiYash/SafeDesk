"""Demo-only protected-mode state manager."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from safedesk.logging.event_logger import EventLogger, build_logger_from_config
from safedesk.protected_mode.protected_models import ProtectedModeActionResult, ProtectedModeState, ProtectedModeStatus
from safedesk.protected_mode.protected_state import (
    default_protected_mode_state,
    load_protected_mode_state,
    resolve_protected_mode_state_path,
    save_protected_mode_state,
    utc_timestamp,
)
from safedesk.threats.threat_state import load_threat_state, resolve_threat_state_path

PROTECTED_ACTIONS = (
    "arm",
    "activate_demo",
    "mark_recovery_required",
    "simulate_recovery_success",
    "simulate_recovery_failure",
    "apply_threat_recommendation",
    "reset",
    "refresh_status",
)


class ProtectedModeManager:
    """Pure local protected-mode foundation manager."""

    def __init__(
        self,
        config: dict,
        state_path: Path | None = None,
        threat_state_path: Path | None = None,
        event_logger: EventLogger | None = None,
    ):
        self.config = config
        self.protected_config = config.get("protected_mode", {})
        self.state_path = state_path or resolve_protected_mode_state_path(config)
        self.threat_state_path = threat_state_path or resolve_threat_state_path(config)
        self.event_logger = event_logger or build_logger_from_config(config)

    @property
    def foundation_enabled(self) -> bool:
        return self.protected_config.get("foundation_enabled", True) is True

    @property
    def demo_only(self) -> bool:
        return self.protected_config.get("demo_only", True) is True

    def load_state(self) -> ProtectedModeState:
        return load_protected_mode_state(self.state_path, self.demo_only)

    def save_state(self, state: ProtectedModeState) -> None:
        save_protected_mode_state(self.state_path, state)

    def build_status(self) -> ProtectedModeStatus:
        """Build a safe status summary without mutating state."""

        state = self.load_state()
        threat_level = self._current_threat_level()
        activation_level = self._candidate_level("activation_candidate_threat_level", 4)
        shutdown_level = self._candidate_level("shutdown_candidate_threat_level", 5)
        activation_recommended = self.protected_config.get("link_threat_level_demo", True) is True and threat_level >= activation_level
        shutdown_recommended = self.protected_config.get("link_threat_level_demo", True) is True and threat_level >= shutdown_level
        if shutdown_recommended:
            recommendation = "Shutdown candidate would be reviewed in a future phase. No shutdown is performed."
        elif activation_recommended:
            recommendation = "Protected mode would be recommended in a future phase. No enforcement is active."
        else:
            recommendation = "No protected-mode recommendation from current threat demo state."
        return ProtectedModeStatus(
            state=state,
            threat_level=threat_level,
            threat_recommendation=recommendation,
            activation_recommended=activation_recommended,
            shutdown_candidate_recommended=shutdown_recommended,
            foundation_enabled=self.foundation_enabled,
            demo_only=self.demo_only,
        )

    def perform_action(self, action: str) -> ProtectedModeActionResult:
        """Apply one manual protected-mode foundation action."""

        state = self.load_state()
        previous_mode = state.mode

        if not self.foundation_enabled:
            return self._result(False, "blocked", previous_mode, state, "Protected mode foundation is disabled in configuration.")

        if action not in PROTECTED_ACTIONS:
            return self._result(False, "invalid_action", previous_mode, state, "Unsupported protected-mode foundation action.")

        if action == "refresh_status":
            return self._result(True, "unchanged", previous_mode, state, "Protected mode status refreshed.")

        if action == "reset":
            return self.reset_state(previous_mode)

        blocked_reason = self._blocked_reason(action)
        if blocked_reason:
            result = self._result(False, "blocked", previous_mode, state, blocked_reason)
            self._log_action(action, result)
            return result

        next_state, reason = self._apply_action(action, state)
        if next_state == state:
            result = self._result(True, "unchanged", previous_mode, next_state, reason)
            self._log_action(action, result)
            return result

        next_state = replace(
            next_state,
            updated_at=utc_timestamp(),
            demo_only=True,
            last_action=action,
            last_reason=reason,
            lockdown_performed=False,
            shutdown_performed=False,
        )
        self.save_state(next_state)
        result = self._result(True, "updated", previous_mode, next_state, reason)
        self._log_action(action, result)
        if next_state.shutdown_candidate:
            self._log_shutdown_candidate(result)
        return result

    def reset_state(self, previous_mode: str | None = None) -> ProtectedModeActionResult:
        previous = previous_mode or self.load_state().mode
        state = default_protected_mode_state(True)
        state = replace(state, mode="inactive", last_action="reset", last_reason="Protected mode state reset to inactive.", updated_at=utc_timestamp())
        self.save_state(state)
        result = self._result(True, "reset", previous, state, "Protected mode state reset to inactive.")
        self._log_action("reset", result)
        return result

    def _blocked_reason(self, action: str) -> str:
        if action == "arm" and self.protected_config.get("allow_manual_arm", True) is not True:
            return "Manual arm is disabled in configuration."
        if action == "activate_demo" and self.protected_config.get("allow_manual_activation", True) is not True:
            return "Manual demo activation is disabled in configuration."
        if action in {"mark_recovery_required", "simulate_recovery_success", "simulate_recovery_failure"} and (
            self.protected_config.get("allow_manual_recovery", True) is not True
        ):
            return "Manual recovery simulation is disabled in configuration."
        if action == "apply_threat_recommendation" and self.protected_config.get("link_threat_level_demo", True) is not True:
            return "Threat level demo link is disabled in configuration."
        return ""

    def _apply_action(self, action: str, state: ProtectedModeState) -> tuple[ProtectedModeState, str]:
        threat_level = self._current_threat_level()
        if action == "arm":
            return (
                replace(
                    state,
                    mode="armed",
                    armed=True,
                    active_demo=False,
                    recovery_required=False,
                    threat_level_at_last_update=threat_level,
                ),
                "Protected mode foundation armed in demo mode.",
            )

        if action == "activate_demo":
            return (
                replace(
                    state,
                    mode="active_demo",
                    armed=True,
                    active_demo=True,
                    recovery_required=False,
                    threat_level_at_last_update=threat_level,
                ),
                "Protected mode demo state activated. No lockdown was performed.",
            )

        if action == "mark_recovery_required":
            return (
                replace(
                    state,
                    mode="recovery_required",
                    armed=True,
                    recovery_required=True,
                    threat_level_at_last_update=threat_level,
                ),
                "Protected mode recovery required state simulated.",
            )

        if action == "simulate_recovery_success":
            return (
                replace(
                    state,
                    mode="recovery_successful",
                    armed=False,
                    active_demo=False,
                    recovery_required=False,
                    threat_level_at_last_update=threat_level,
                    shutdown_candidate=False,
                ),
                "Owner recovery simulation completed.",
            )

        if action == "simulate_recovery_failure":
            return (
                replace(
                    state,
                    mode="recovery_required",
                    armed=True,
                    recovery_required=True,
                    threat_level_at_last_update=threat_level,
                ),
                "Owner recovery simulation did not succeed. No shutdown or lockdown was performed.",
            )

        if action == "apply_threat_recommendation":
            return self._apply_threat_recommendation(state, threat_level)

        return state, "Protected mode status refreshed."

    def _apply_threat_recommendation(self, state: ProtectedModeState, threat_level: int) -> tuple[ProtectedModeState, str]:
        if self.protected_config.get("link_threat_level_demo", True) is not True:
            return state, "Threat level demo link is disabled in configuration."
        activation_level = self._candidate_level("activation_candidate_threat_level", 4)
        shutdown_level = self._candidate_level("shutdown_candidate_threat_level", 5)
        shutdown_candidate = threat_level >= shutdown_level
        if threat_level >= activation_level:
            return (
                replace(
                    state,
                    mode="armed",
                    armed=True,
                    active_demo=False,
                    recovery_required=state.recovery_required,
                    threat_level_at_last_update=threat_level,
                    shutdown_candidate=shutdown_candidate,
                ),
                "Threat recommendation applied manually. No enforcement action was performed.",
            )
        return (
            replace(
                state,
                threat_level_at_last_update=threat_level,
                shutdown_candidate=False,
            ),
            "Current threat demo state does not recommend protected mode.",
        )

    def _current_threat_level(self) -> int:
        if self.protected_config.get("link_threat_level_demo", True) is not True:
            return 0
        threat_state = load_threat_state(self.threat_state_path)
        return max(0, min(5, int(threat_state.current_level)))

    def _candidate_level(self, key: str, default: int) -> int:
        value = self.protected_config.get(key, default)
        if isinstance(value, bool) or not isinstance(value, int):
            return default
        return max(0, min(5, value))

    @staticmethod
    def _result(
        success: bool,
        status: str,
        previous_mode: str,
        state: ProtectedModeState,
        reason: str,
    ) -> ProtectedModeActionResult:
        if state.shutdown_candidate:
            message = "Shutdown candidate marked in protected-mode demo state. No shutdown was performed."
        elif status == "reset":
            message = "Protected mode state reset to inactive."
        elif success:
            message = reason
        else:
            message = reason
        return ProtectedModeActionResult(
            success=success,
            status=status,
            previous_mode=previous_mode,
            new_mode=state.mode,
            message=message,
            state=state,
        )

    def _log_action(self, action: str, result: ProtectedModeActionResult) -> None:
        action_name = {
            "arm": "protected_mode_armed",
            "activate_demo": "protected_mode_demo_activated",
            "mark_recovery_required": "protected_mode_recovery_required",
            "simulate_recovery_success": "protected_mode_recovery_successful",
            "simulate_recovery_failure": "protected_mode_recovery_failed",
            "apply_threat_recommendation": "protected_mode_threat_recommendation_applied",
            "reset": "protected_mode_reset",
        }.get(action, "protected_mode_status_checked")
        message = {
            "arm": "Protected mode foundation armed in demo mode.",
            "activate_demo": "Protected mode demo state activated. No lockdown was performed.",
            "mark_recovery_required": "Protected mode recovery required state simulated.",
            "simulate_recovery_success": "Owner recovery simulation completed.",
            "simulate_recovery_failure": "Owner recovery simulation did not succeed. No shutdown or lockdown was performed.",
            "apply_threat_recommendation": "Threat recommendation applied manually. No enforcement action was performed.",
            "reset": "Protected mode state reset to inactive.",
        }.get(action, "Protected mode foundation status checked.")
        severity = "WARNING" if result.state.shutdown_candidate or result.state.recovery_required else "INFO"
        self._safe_log(action_name, "success" if result.success else "blocked", severity, message, result)

    def _log_shutdown_candidate(self, result: ProtectedModeActionResult) -> None:
        self._safe_log(
            "protected_mode_shutdown_candidate",
            "info",
            "WARNING",
            "Shutdown candidate marked in protected-mode demo state. No shutdown was performed.",
            result,
        )

    def _safe_log(self, action: str, status: str, severity: str, message: str, result: ProtectedModeActionResult) -> None:
        try:
            self.event_logger.log_event(
                category="protected_mode",
                action=action,
                status=status,
                severity=severity,
                message=message,
                metadata={
                    "previous_mode": result.previous_mode,
                    "new_mode": result.new_mode,
                    "armed": result.state.armed,
                    "active_demo": result.state.active_demo,
                    "recovery_required": result.state.recovery_required,
                    "threat_level": result.state.threat_level_at_last_update,
                    "shutdown_candidate": result.state.shutdown_candidate,
                    "demo_only": True,
                    "lockdown_performed": False,
                    "shutdown_performed": False,
                    "protected_enforcement_active": False,
                },
            )
        except Exception:
            pass


def build_protected_mode_manager_from_config(config: dict, state_path: Path | None = None) -> ProtectedModeManager:
    """Build a protected-mode manager from runtime config."""

    return ProtectedModeManager(config, state_path=state_path)

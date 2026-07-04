"""Demo-only shutdown escalation dry-run manager."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from safedesk.logging.event_logger import EventLogger, build_logger_from_config
from safedesk.protected_mode.protected_state import load_protected_mode_state, resolve_protected_mode_state_path
from safedesk.shutdown_escalation.real_shutdown_executor import RealShutdownExecutor
from safedesk.shutdown_escalation.shutdown_guard import ShutdownGuardReport, evaluate_shutdown_guards
from safedesk.shutdown_escalation.shutdown_models import (
    SHUTDOWN_ACTIONS,
    ShutdownEscalationActionResult,
    ShutdownEscalationState,
    ShutdownEscalationStatus,
)
from safedesk.shutdown_escalation.shutdown_state import (
    default_shutdown_state,
    load_shutdown_state,
    resolve_shutdown_state_path,
    save_shutdown_state,
    utc_timestamp,
)
from safedesk.threats.threat_state import load_threat_state, resolve_threat_state_path


class ShutdownEscalationManager:
    """Pure local shutdown escalation foundation manager."""

    def __init__(
        self,
        config: dict,
        state_path: Path | None = None,
        threat_state_path: Path | None = None,
        protected_state_path: Path | None = None,
        event_logger: EventLogger | None = None,
        executor: RealShutdownExecutor | None = None,
        platform_name: str | None = None,
    ):
        self.config = config
        self.shutdown_config = config.get("shutdown", {})
        self.state_path = state_path or resolve_shutdown_state_path(config)
        self.threat_state_path = threat_state_path or resolve_threat_state_path(config)
        self.protected_state_path = protected_state_path or resolve_protected_mode_state_path(config)
        self.event_logger = event_logger or build_logger_from_config(config)
        self.platform_name = platform_name
        self.executor = executor or RealShutdownExecutor(platform_name=platform_name)

    @property
    def foundation_enabled(self) -> bool:
        return self.shutdown_config.get("foundation_enabled", True) is True

    @property
    def demo_only(self) -> bool:
        return self.shutdown_config.get("demo_shutdown_only", True) is True

    @property
    def manual_confirmation_required(self) -> bool:
        return self.shutdown_config.get("require_manual_confirmation", True) is True

    @property
    def real_shutdown_enabled(self) -> bool:
        return self.shutdown_config.get("real_shutdown_enabled", False) is True

    @property
    def real_shutdown_command_enabled(self) -> bool:
        return self.shutdown_config.get("real_shutdown_command_enabled", False) is True

    def load_state(self) -> ShutdownEscalationState:
        return load_shutdown_state(self.state_path, self.demo_only, self.manual_confirmation_required)

    def save_state(self, state: ShutdownEscalationState) -> None:
        save_shutdown_state(self.state_path, self._safe_state(state))

    def build_status(self) -> ShutdownEscalationStatus:
        """Build a safe status summary without mutating state."""

        state = self.load_state()
        threat_level = self._current_threat_level()
        protected_state = self._current_protected_state()
        guard_report = self.evaluate_real_shutdown_guards()
        threshold = self._shutdown_after_threat_level()
        link_threat = self.shutdown_config.get("link_threat_level_demo", True) is True
        link_protected = self.shutdown_config.get("link_protected_mode_demo", True) is True
        threat_recommended = link_threat and threat_level >= threshold
        protected_recommended = link_protected and protected_state.shutdown_candidate
        if threat_recommended or protected_recommended:
            recommendation = "Shutdown escalation would be reviewed in a future phase. No shutdown is performed."
        else:
            recommendation = "No shutdown escalation recommendation from current demo state."
        return ShutdownEscalationStatus(
            state=state,
            threat_level=threat_level,
            protected_mode=protected_state.mode,
            protected_shutdown_candidate=protected_state.shutdown_candidate,
            shutdown_recommended=threat_recommended or protected_recommended,
            foundation_enabled=self.foundation_enabled,
            demo_only=self.demo_only,
            real_shutdown_enabled=self.real_shutdown_enabled,
            real_shutdown_command_enabled=self.real_shutdown_command_enabled,
            guarded_real_shutdown_ready=guard_report.ready,
            platform_supported=guard_report.platform_supported,
            recommendation=recommendation,
        )

    def evaluate_real_shutdown_guards(self) -> ShutdownGuardReport:
        """Evaluate guarded real shutdown prerequisites without executing anything."""

        return evaluate_shutdown_guards(self.config, platform_name=self.platform_name)

    def check_real_shutdown_guards(self) -> ShutdownEscalationActionResult:
        """Run guard checks only. This never schedules shutdown."""

        state = self.load_state()
        previous_mode = state.mode
        report = self.evaluate_real_shutdown_guards()
        next_state = replace(
            state,
            guarded_real_shutdown_ready=report.ready,
            real_shutdown_platform=self._executor_platform_name(),
            real_shutdown_result_status="guards_ready" if report.ready else "guards_blocked",
            real_shutdown_result_message=report.message,
            real_shutdown_enabled=self.real_shutdown_enabled,
            real_shutdown_command_enabled=self.real_shutdown_command_enabled,
            updated_at=utc_timestamp(),
            last_action="check_real_shutdown_guards",
            last_reason=report.message,
            shutdown_performed=False,
            restart_performed=False,
            logoff_performed=False,
            lockdown_performed=False,
            alarm_performed=False,
            email_sent=False,
        )
        self.save_state(next_state)
        result = self._result(True, "updated", previous_mode, next_state, report.message)
        self._log_real_shutdown_event(
            "real_shutdown_guards_checked",
            "success",
            "WARNING" if report.ready else "INFO",
            "Real shutdown guard checks completed.",
            result,
            guard_report=report,
            confirmation_matched=False,
        )
        return result

    def request_guarded_real_shutdown(self, confirmation_phrase: str) -> ShutdownEscalationActionResult:
        """Request a guarded Windows shutdown. This is the only scheduling path."""

        state = self.load_state()
        previous_mode = state.mode
        report = self.evaluate_real_shutdown_guards()
        configured_phrase = self.shutdown_config.get("real_shutdown_confirmation_phrase", "")
        confirmation_matched = isinstance(confirmation_phrase, str) and confirmation_phrase == configured_phrase

        if not report.ready:
            next_state = self._real_shutdown_state(
                state,
                report,
                confirmation_matched=confirmation_matched,
                requested=False,
                scheduled=False,
                result_status="guards_blocked",
                result_message="Real shutdown request blocked by guard checks.",
            )
            self.save_state(next_state)
            result = self._result(False, "blocked", previous_mode, next_state, "Real shutdown request blocked by guard checks.")
            self._log_real_shutdown_event(
                "real_shutdown_request_blocked",
                "blocked",
                "WARNING",
                "Real shutdown request blocked by guard checks.",
                result,
                guard_report=report,
                confirmation_matched=confirmation_matched,
            )
            return result

        if not confirmation_matched:
            next_state = self._real_shutdown_state(
                state,
                report,
                confirmation_matched=False,
                requested=False,
                scheduled=False,
                result_status="confirmation_failed",
                result_message="Real shutdown confirmation phrase did not match.",
            )
            self.save_state(next_state)
            result = self._result(False, "blocked", previous_mode, next_state, "Real shutdown confirmation phrase did not match.")
            self._log_real_shutdown_event(
                "real_shutdown_confirmation_failed",
                "blocked",
                "WARNING",
                "Real shutdown confirmation phrase did not match.",
                result,
                guard_report=report,
                confirmation_matched=False,
            )
            return result

        countdown_seconds = self._real_shutdown_countdown_seconds()
        execution_result = self.executor.schedule_windows_shutdown(
            countdown_seconds,
            "SafeDesk guarded shutdown test",
        )
        next_state = self._real_shutdown_state(
            state,
            report,
            confirmation_matched=True,
            requested=True,
            scheduled=execution_result.success,
            result_status=execution_result.status,
            result_message=execution_result.message,
        )
        self.save_state(next_state)
        status = "updated" if execution_result.success else "blocked"
        result = self._result(execution_result.success, status, previous_mode, next_state, execution_result.message)
        self._log_real_shutdown_event(
            "real_shutdown_scheduled" if execution_result.success else "real_shutdown_request_blocked",
            "success" if execution_result.success else "blocked",
            "WARNING",
            "Guarded Windows shutdown was scheduled manually." if execution_result.success else "Real shutdown request blocked by guard checks.",
            result,
            guard_report=report,
            confirmation_matched=True,
        )
        return result

    def abort_pending_real_shutdown(self) -> ShutdownEscalationActionResult:
        """Abort a pending guarded Windows shutdown if local config allows it."""

        state = self.load_state()
        previous_mode = state.mode
        report = self.evaluate_real_shutdown_guards()
        if self.shutdown_config.get("allow_abort_real_shutdown", True) is not True:
            next_state = replace(
                state,
                real_shutdown_abort_requested=False,
                real_shutdown_aborted=False,
                real_shutdown_result_status="abort_blocked",
                real_shutdown_result_message="Pending Windows shutdown abort was blocked safely.",
                updated_at=utc_timestamp(),
                last_action="abort_pending_real_shutdown",
                last_reason="Pending Windows shutdown abort was blocked safely.",
            )
            self.save_state(next_state)
            result = self._result(False, "blocked", previous_mode, next_state, "Pending Windows shutdown abort was blocked safely.")
            self._log_real_shutdown_event(
                "real_shutdown_abort_blocked",
                "blocked",
                "WARNING",
                "Pending Windows shutdown abort was blocked safely.",
                result,
                guard_report=report,
                confirmation_matched=False,
            )
            return result

        self._log_real_shutdown_event(
            "real_shutdown_abort_requested",
            "info",
            "WARNING",
            "Pending Windows shutdown abort was requested manually.",
            self._result(True, "updated", previous_mode, state, "Pending Windows shutdown abort was requested manually."),
            guard_report=report,
            confirmation_matched=False,
        )
        execution_result = self.executor.abort_windows_shutdown()
        next_state = replace(
            state,
            guarded_real_shutdown_ready=report.ready,
            real_shutdown_abort_requested=True,
            real_shutdown_aborted=execution_result.success,
            real_shutdown_scheduled=False if execution_result.success else state.real_shutdown_scheduled,
            real_shutdown_result_status=execution_result.status,
            real_shutdown_result_message=execution_result.message,
            updated_at=utc_timestamp(),
            last_action="abort_pending_real_shutdown",
            last_reason=execution_result.message,
            shutdown_performed=False,
            restart_performed=False,
            logoff_performed=False,
            lockdown_performed=False,
            alarm_performed=False,
            email_sent=False,
        )
        self.save_state(next_state)
        result = self._result(execution_result.success, "updated" if execution_result.success else "blocked", previous_mode, next_state, execution_result.message)
        self._log_real_shutdown_event(
            "real_shutdown_abort_completed" if execution_result.success else "real_shutdown_abort_blocked",
            "success" if execution_result.success else "blocked",
            "WARNING",
            "Pending Windows shutdown abort completed." if execution_result.success else "Pending Windows shutdown abort was blocked safely.",
            result,
            guard_report=report,
            confirmation_matched=False,
        )
        return result

    def perform_action(self, action: str) -> ShutdownEscalationActionResult:
        """Apply one manual shutdown escalation dry-run action."""

        state = self.load_state()
        previous_mode = state.mode

        if action not in SHUTDOWN_ACTIONS:
            return self._result(False, "invalid_action", previous_mode, state, "Unsupported shutdown escalation dry-run action.")

        if action == "reset":
            return self.reset_state(previous_mode)

        if action == "refresh_status":
            return self._result(True, "unchanged", previous_mode, state, "Shutdown escalation dry-run status refreshed.")

        config_block = self._config_block_reason()
        if config_block:
            return self._blocked_by_config(previous_mode, state, config_block)

        blocked_reason = self._blocked_action_reason(action, state)
        if blocked_reason:
            result = self._result(False, "blocked", previous_mode, state, blocked_reason)
            self._log_action(action, result)
            return result

        next_state, reason = self._apply_action(action, state)
        next_state = replace(
            next_state,
            updated_at=utc_timestamp(),
            demo_only=True,
            last_action=action,
            last_reason=reason,
            manual_confirmation_required=self.manual_confirmation_required,
            real_shutdown_enabled=False,
            real_shutdown_command_enabled=False,
            shutdown_performed=False,
            restart_performed=False,
            logoff_performed=False,
            lockdown_performed=False,
            alarm_performed=False,
            email_sent=False,
        )
        self.save_state(next_state)
        status = "unchanged" if next_state == state else "updated"
        result = self._result(True, status, previous_mode, next_state, reason)
        if action != "tick_demo_countdown" or next_state.mode == "simulated_shutdown_completed":
            self._log_action(action, result)
        return result

    def reset_state(self, previous_mode: str | None = None) -> ShutdownEscalationActionResult:
        previous = previous_mode or self.load_state().mode
        state = default_shutdown_state(True, self.manual_confirmation_required)
        state = replace(state, mode="idle", last_action="reset", last_reason="Shutdown escalation state reset to idle.", updated_at=utc_timestamp())
        self.save_state(state)
        result = self._result(True, "reset", previous, state, "Shutdown escalation state reset to idle.")
        self._log_action("reset", result)
        return result

    def _apply_action(self, action: str, state: ShutdownEscalationState) -> tuple[ShutdownEscalationState, str]:
        threat_level = self._current_threat_level()
        protected_state = self._current_protected_state()

        if action == "mark_shutdown_candidate":
            return (
                replace(
                    state,
                    mode="candidate",
                    shutdown_candidate=True,
                    countdown_running=False,
                    threat_level_at_last_update=threat_level,
                    protected_mode_at_last_update=protected_state.mode,
                    protected_shutdown_candidate=protected_state.shutdown_candidate,
                ),
                "Shutdown escalation candidate marked in demo mode. No shutdown was performed.",
            )

        if action == "apply_protected_mode_candidate":
            if protected_state.shutdown_candidate:
                return (
                    replace(
                        state,
                        mode="candidate",
                        shutdown_candidate=True,
                        countdown_running=False,
                        protected_mode_at_last_update=protected_state.mode,
                        protected_shutdown_candidate=True,
                        threat_level_at_last_update=threat_level,
                    ),
                    "Protected-mode shutdown candidate applied manually. No shutdown was performed.",
                )
            return (
                replace(
                    state,
                    protected_mode_at_last_update=protected_state.mode,
                    protected_shutdown_candidate=False,
                    threat_level_at_last_update=threat_level,
                ),
                "Protected-mode demo state reviewed. No shutdown candidate is active.",
            )

        if action == "apply_threat_level_candidate":
            if threat_level >= self._shutdown_after_threat_level():
                return (
                    replace(
                        state,
                        mode="candidate",
                        shutdown_candidate=True,
                        countdown_running=False,
                        threat_level_at_last_update=threat_level,
                        protected_mode_at_last_update=protected_state.mode,
                        protected_shutdown_candidate=protected_state.shutdown_candidate,
                    ),
                    "Threat-level shutdown candidate applied manually. No shutdown was performed.",
                )
            return (
                replace(
                    state,
                    threat_level_at_last_update=threat_level,
                    protected_mode_at_last_update=protected_state.mode,
                    protected_shutdown_candidate=protected_state.shutdown_candidate,
                ),
                "Current threat demo state does not recommend shutdown escalation.",
            )

        if action == "prepare_demo_countdown":
            return (
                replace(
                    state,
                    mode="countdown_ready",
                    countdown_running=False,
                    countdown_remaining_seconds=self._countdown_seconds(),
                    countdown_total_seconds=self._countdown_seconds(),
                    threat_level_at_last_update=threat_level,
                    protected_mode_at_last_update=protected_state.mode,
                    protected_shutdown_candidate=protected_state.shutdown_candidate,
                ),
                "Demo shutdown countdown prepared. No shutdown command is connected.",
            )

        if action == "start_demo_countdown":
            remaining = state.countdown_remaining_seconds if state.countdown_remaining_seconds > 0 else self._countdown_seconds()
            return (
                replace(
                    state,
                    mode="countdown_running",
                    countdown_running=True,
                    countdown_remaining_seconds=remaining,
                    countdown_total_seconds=self._countdown_seconds(),
                    threat_level_at_last_update=threat_level,
                    protected_mode_at_last_update=protected_state.mode,
                    protected_shutdown_candidate=protected_state.shutdown_candidate,
                ),
                "Demo shutdown countdown started. No shutdown will be performed.",
            )

        if action == "tick_demo_countdown":
            remaining = max(0, state.countdown_remaining_seconds - 1)
            if remaining <= 0:
                return self._completed_state(state), "Demo shutdown countdown completed. No shutdown was performed."
            return replace(state, countdown_remaining_seconds=remaining, countdown_running=True, mode="countdown_running"), "Demo countdown tick."

        if action == "complete_demo_countdown_now":
            return self._completed_state(state), "Demo shutdown countdown completed. No shutdown was performed."

        if action == "cancel_countdown":
            return (
                replace(
                    state,
                    mode="cancelled",
                    shutdown_candidate=False,
                    countdown_running=False,
                    countdown_remaining_seconds=0,
                    countdown_total_seconds=max(0, state.countdown_total_seconds),
                ),
                "Demo shutdown countdown cancelled. No shutdown was performed.",
            )

        if action == "mark_recovery_successful":
            return (
                replace(
                    state,
                    mode="recovery_cancelled",
                    shutdown_candidate=False,
                    countdown_running=False,
                    countdown_remaining_seconds=0,
                ),
                "Recovery simulation cancelled shutdown escalation. No shutdown was performed.",
            )

        return state, "Shutdown escalation dry-run status refreshed."

    @staticmethod
    def _completed_state(state: ShutdownEscalationState) -> ShutdownEscalationState:
        return replace(
            state,
            mode="simulated_shutdown_completed",
            shutdown_candidate=False,
            countdown_running=False,
            countdown_remaining_seconds=0,
            shutdown_performed=False,
            restart_performed=False,
            logoff_performed=False,
            lockdown_performed=False,
            alarm_performed=False,
            email_sent=False,
        )

    def _blocked_action_reason(self, action: str, state: ShutdownEscalationState) -> str:
        if action == "apply_threat_level_candidate" and self.shutdown_config.get("link_threat_level_demo", True) is not True:
            return "Threat level demo link is disabled in configuration."
        if action == "apply_protected_mode_candidate" and self.shutdown_config.get("link_protected_mode_demo", True) is not True:
            return "Protected-mode demo link is disabled in configuration."
        if action in {"prepare_demo_countdown", "start_demo_countdown"} and not state.shutdown_candidate:
            return "A shutdown candidate must be marked before preparing or starting the demo countdown."
        if action in {"start_demo_countdown", "tick_demo_countdown", "complete_demo_countdown_now"} and (
            self.shutdown_config.get("allow_demo_countdown", True) is not True
        ):
            return "Demo countdown is disabled in configuration."
        if action == "tick_demo_countdown" and not state.countdown_running:
            return "No demo shutdown countdown is running."
        if action == "cancel_countdown" and self.shutdown_config.get("allow_cancel", True) is not True:
            return "Countdown cancellation is disabled in configuration."
        if action == "mark_recovery_successful" and self.shutdown_config.get("allow_recovery_cancel", True) is not True:
            return "Recovery cancellation is disabled in configuration."
        return ""

    def _config_block_reason(self) -> str:
        if not self.foundation_enabled:
            return "Shutdown escalation foundation is disabled in configuration."
        real_shutdown_related = (
            self.real_shutdown_enabled
            or self.real_shutdown_command_enabled
            or self.shutdown_config.get("allow_guarded_real_shutdown") is True
            or self.shutdown_config.get("demo_shutdown_only") is False
            or self.config.get("feature_flags", {}).get("enable_real_shutdown") is True
        )
        if real_shutdown_related and not self.evaluate_real_shutdown_guards().ready:
            return "Shutdown escalation dry-run is blocked because real shutdown configuration is incomplete."
        return ""

    def _blocked_by_config(
        self,
        previous_mode: str,
        state: ShutdownEscalationState,
        reason: str,
    ) -> ShutdownEscalationActionResult:
        blocked_state = replace(
            state,
            mode="blocked_by_config",
            shutdown_candidate=False,
            countdown_running=False,
            countdown_remaining_seconds=0,
            last_action="blocked_by_config",
            last_reason=reason,
            updated_at=utc_timestamp(),
            demo_only=True,
            manual_confirmation_required=self.manual_confirmation_required,
            real_shutdown_enabled=False,
            real_shutdown_command_enabled=False,
            shutdown_performed=False,
            restart_performed=False,
            logoff_performed=False,
            lockdown_performed=False,
            alarm_performed=False,
            email_sent=False,
        )
        self.save_state(blocked_state)
        result = self._result(False, "blocked", previous_mode, blocked_state, reason)
        self._safe_log(
            "shutdown_blocked_by_config",
            "blocked",
            "WARNING",
            "Shutdown escalation blocked by configuration.",
            result,
        )
        return result

    def _current_threat_level(self) -> int:
        if self.shutdown_config.get("link_threat_level_demo", True) is not True:
            return 0
        threat_state = load_threat_state(self.threat_state_path)
        return max(0, min(5, int(threat_state.current_level)))

    def _current_protected_state(self):
        if self.shutdown_config.get("link_protected_mode_demo", True) is not True:
            return load_protected_mode_state(self.protected_state_path)
        return load_protected_mode_state(self.protected_state_path)

    def _shutdown_after_threat_level(self) -> int:
        value = self.shutdown_config.get("shutdown_after_threat_level", 5)
        if isinstance(value, bool) or not isinstance(value, int):
            return 5
        return max(0, min(5, value))

    def _countdown_seconds(self) -> int:
        value = self.shutdown_config.get("countdown_seconds", 30)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            return 30
        return max(1, min(3600, value))

    def _real_shutdown_countdown_seconds(self) -> int:
        value = self.shutdown_config.get("real_shutdown_countdown_seconds", 60)
        if isinstance(value, bool) or not isinstance(value, int) or value < 30:
            return 60
        return max(30, min(3600, value))

    def _executor_platform_name(self) -> str:
        return str(getattr(self.executor, "platform_name", self.platform_name or ""))

    @staticmethod
    def _result(
        success: bool,
        status: str,
        previous_mode: str,
        state: ShutdownEscalationState,
        reason: str,
    ) -> ShutdownEscalationActionResult:
        return ShutdownEscalationActionResult(
            success=success,
            status=status,
            previous_mode=previous_mode,
            new_mode=state.mode,
            message=reason,
            state=state,
        )

    @staticmethod
    def _safe_state(state: ShutdownEscalationState) -> ShutdownEscalationState:
        return replace(
            state,
            demo_only=True,
            shutdown_performed=False,
            restart_performed=False,
            logoff_performed=False,
            lockdown_performed=False,
            alarm_performed=False,
            email_sent=False,
        )

    def _real_shutdown_state(
        self,
        state: ShutdownEscalationState,
        report: ShutdownGuardReport,
        confirmation_matched: bool,
        requested: bool,
        scheduled: bool,
        result_status: str,
        result_message: str,
    ) -> ShutdownEscalationState:
        return replace(
            state,
            guarded_real_shutdown_ready=report.ready,
            real_shutdown_confirmation_matched=confirmation_matched,
            real_shutdown_requested=requested,
            real_shutdown_scheduled=scheduled,
            real_shutdown_countdown_seconds=self._real_shutdown_countdown_seconds(),
            real_shutdown_platform=self._executor_platform_name(),
            real_shutdown_result_status=result_status,
            real_shutdown_result_message=result_message,
            real_shutdown_enabled=self.real_shutdown_enabled,
            real_shutdown_command_enabled=self.real_shutdown_command_enabled,
            updated_at=utc_timestamp(),
            last_action="request_guarded_real_shutdown",
            last_reason=result_message,
            shutdown_performed=False,
            restart_performed=False,
            logoff_performed=False,
            lockdown_performed=False,
            alarm_performed=False,
            email_sent=False,
        )

    def _log_action(self, action: str, result: ShutdownEscalationActionResult) -> None:
        action_name = {
            "mark_shutdown_candidate": "shutdown_candidate_marked",
            "apply_protected_mode_candidate": "shutdown_protected_candidate_applied",
            "apply_threat_level_candidate": "shutdown_threat_candidate_applied",
            "prepare_demo_countdown": "shutdown_demo_countdown_prepared",
            "start_demo_countdown": "shutdown_demo_countdown_started",
            "tick_demo_countdown": "shutdown_demo_countdown_completed",
            "complete_demo_countdown_now": "shutdown_demo_countdown_completed",
            "cancel_countdown": "shutdown_demo_countdown_cancelled",
            "mark_recovery_successful": "shutdown_recovery_cancelled",
            "reset": "shutdown_state_reset",
        }.get(action, "shutdown_status_checked")
        message = {
            "mark_shutdown_candidate": "Shutdown escalation candidate marked in demo mode. No shutdown was performed.",
            "apply_protected_mode_candidate": "Protected-mode shutdown candidate reviewed manually. No shutdown was performed.",
            "apply_threat_level_candidate": "Threat-level shutdown candidate reviewed manually. No shutdown was performed.",
            "prepare_demo_countdown": "Demo shutdown countdown prepared. No shutdown command is connected.",
            "start_demo_countdown": "Demo shutdown countdown started. No shutdown will be performed.",
            "tick_demo_countdown": "Demo shutdown countdown completed. No shutdown was performed.",
            "complete_demo_countdown_now": "Demo shutdown countdown completed. No shutdown was performed.",
            "cancel_countdown": "Demo shutdown countdown cancelled. No shutdown was performed.",
            "mark_recovery_successful": "Recovery simulation cancelled shutdown escalation. No shutdown was performed.",
            "reset": "Shutdown escalation state reset to idle.",
        }.get(action, "Shutdown escalation dry-run status checked.")
        if result.status == "blocked":
            message = "Shutdown escalation dry-run action was blocked safely."
        severity = "WARNING" if result.state.shutdown_candidate or result.state.mode in {"countdown_running", "simulated_shutdown_completed"} else "INFO"
        status = "blocked" if result.status == "blocked" else "success"
        self._safe_log(action_name, status, severity, message, result)

    def _safe_log(
        self,
        action: str,
        status: str,
        severity: str,
        message: str,
        result: ShutdownEscalationActionResult,
    ) -> None:
        try:
            self.event_logger.log_event(
                category="shutdown_escalation",
                action=action,
                status=status,
                severity=severity,
                message=message,
                metadata={
                    "previous_mode": result.previous_mode,
                    "new_mode": result.new_mode,
                    "shutdown_candidate": result.state.shutdown_candidate,
                    "countdown_running": result.state.countdown_running,
                    "countdown_remaining_seconds": result.state.countdown_remaining_seconds,
                    "countdown_total_seconds": result.state.countdown_total_seconds,
                    "threat_level": result.state.threat_level_at_last_update,
                    "protected_mode": result.state.protected_mode_at_last_update,
                    "protected_shutdown_candidate": result.state.protected_shutdown_candidate,
                    "manual_confirmation_required": result.state.manual_confirmation_required,
                    "demo_only": True,
                    "real_shutdown_enabled": False,
                    "real_shutdown_command_enabled": False,
                    "shutdown_performed": False,
                    "restart_performed": False,
                    "logoff_performed": False,
                    "lockdown_performed": False,
                    "alarm_performed": False,
                    "email_sent": False,
                    "protected_enforcement_active": False,
                },
            )
        except Exception:
            pass

    def _log_real_shutdown_event(
        self,
        action: str,
        status: str,
        severity: str,
        message: str,
        result: ShutdownEscalationActionResult,
        guard_report: ShutdownGuardReport,
        confirmation_matched: bool,
    ) -> None:
        try:
            self.event_logger.log_event(
                category="shutdown_escalation",
                action=action,
                status=status,
                severity=severity,
                message=message,
                metadata={
                    "guard_ready": guard_report.ready,
                    "platform_supported": guard_report.platform_supported,
                    "confirmation_matched": confirmation_matched,
                    "real_shutdown_countdown_seconds": result.state.real_shutdown_countdown_seconds,
                    "real_shutdown_requested": result.state.real_shutdown_requested,
                    "real_shutdown_scheduled": result.state.real_shutdown_scheduled,
                    "real_shutdown_abort_requested": result.state.real_shutdown_abort_requested,
                    "real_shutdown_aborted": result.state.real_shutdown_aborted,
                    "real_shutdown_result_status": result.state.real_shutdown_result_status,
                    "demo_only": self.demo_only,
                    "manual_confirmation_required": self.manual_confirmation_required,
                    "shutdown_performed": False,
                    "restart_performed": False,
                    "logoff_performed": False,
                    "lockdown_performed": False,
                    "alarm_performed": False,
                    "email_sent": False,
                    "protected_enforcement_active": False,
                },
            )
        except Exception:
            pass


def build_shutdown_escalation_manager_from_config(
    config: dict,
    state_path: Path | None = None,
) -> ShutdownEscalationManager:
    """Build a shutdown escalation dry-run manager from runtime config."""

    return ShutdownEscalationManager(config, state_path=state_path)

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.protected_mode.protected_manager import ProtectedModeManager
from safedesk.shutdown_escalation.real_shutdown_executor import RealShutdownExecutionResult
from safedesk.shutdown_escalation.shutdown_manager import ShutdownEscalationManager
from safedesk.threats.threat_manager import ThreatManager


class FakeShutdownExecutor:
    def __init__(self):
        self.scheduled_countdowns = []
        self.abort_calls = 0

    def schedule_windows_shutdown(self, countdown_seconds, comment=""):
        self.scheduled_countdowns.append((countdown_seconds, comment))
        return RealShutdownExecutionResult(True, "scheduled", f"Scheduled for {countdown_seconds} seconds.", countdown_seconds)

    def abort_windows_shutdown(self):
        self.abort_calls += 1
        return RealShutdownExecutionResult(True, "aborted", "Abort completed.")


def _config_for(tmp_path, shutdown_overrides=None, real_shutdown=False):
    real_config = (
        {
            "feature_flags": {"enable_real_shutdown": True},
            "app": {"demo_safe_mode": False},
            "security_mode": {"default_mode": "standard"},
        }
        if real_shutdown
        else {}
    )
    return deep_merge(
        deep_merge(DEFAULT_CONFIG, real_config),
        {
            "shutdown": {
                "state_path": str(tmp_path / "shutdown_state.json"),
                "countdown_seconds": 2,
                **(
                    {
                        "allow_guarded_real_shutdown": True,
                        "real_shutdown_enabled": True,
                        "real_shutdown_command_enabled": True,
                        "demo_shutdown_only": False,
                        "real_shutdown_countdown_seconds": 60,
                        "allow_abort_real_shutdown": True,
                    }
                    if real_shutdown
                    else {}
                ),
                **(shutdown_overrides or {}),
            },
            "protected_mode": {
                "state_path": str(tmp_path / "protected_mode_state.json"),
                "activation_candidate_threat_level": 4,
                "shutdown_candidate_threat_level": 5,
            },
            "threat_levels": {
                "state_path": str(tmp_path / "threat_state.json"),
            },
            "logging": {
                "enabled": True,
                "database_path": str(tmp_path / "safedesk.sqlite3"),
                "demo_only": True,
            },
        },
    )


def test_mark_shutdown_candidate_sets_safe_candidate_state(tmp_path):
    manager = ShutdownEscalationManager(_config_for(tmp_path))

    result = manager.perform_action("mark_shutdown_candidate")

    assert result.success is True
    assert result.new_mode == "candidate"
    assert result.state.shutdown_candidate is True
    assert result.state.shutdown_performed is False
    assert "No shutdown was performed" in result.message


def test_prepare_start_and_tick_countdown_completes_without_shutdown(tmp_path):
    manager = ShutdownEscalationManager(_config_for(tmp_path))
    manager.perform_action("mark_shutdown_candidate")
    manager.perform_action("prepare_demo_countdown")

    started = manager.perform_action("start_demo_countdown")
    tick_one = manager.perform_action("tick_demo_countdown")
    completed = manager.perform_action("tick_demo_countdown")

    assert started.state.countdown_running is True
    assert tick_one.state.countdown_remaining_seconds == 1
    assert completed.new_mode == "simulated_shutdown_completed"
    assert completed.state.shutdown_performed is False
    assert completed.state.restart_performed is False
    assert completed.state.lockdown_performed is False
    assert completed.state.alarm_performed is False
    assert completed.state.email_sent is False
    assert completed.message == "Demo shutdown countdown completed. No shutdown was performed."


def test_tick_does_not_log_every_second(tmp_path):
    manager = ShutdownEscalationManager(_config_for(tmp_path))
    manager.perform_action("mark_shutdown_candidate")
    manager.perform_action("prepare_demo_countdown")
    manager.perform_action("start_demo_countdown")
    before_tick = manager.event_logger.store.count_events()

    manager.perform_action("tick_demo_countdown")
    after_non_final_tick = manager.event_logger.store.count_events()
    manager.perform_action("tick_demo_countdown")
    after_completion = manager.event_logger.store.count_events()

    assert after_non_final_tick == before_tick
    assert after_completion == before_tick + 1


def test_cancel_countdown_clears_candidate_and_running_state(tmp_path):
    manager = ShutdownEscalationManager(_config_for(tmp_path))
    manager.perform_action("mark_shutdown_candidate")
    manager.perform_action("start_demo_countdown")

    result = manager.perform_action("cancel_countdown")

    assert result.new_mode == "cancelled"
    assert result.state.shutdown_candidate is False
    assert result.state.countdown_running is False


def test_recovery_success_cancels_shutdown_path(tmp_path):
    manager = ShutdownEscalationManager(_config_for(tmp_path))
    manager.perform_action("mark_shutdown_candidate")

    result = manager.perform_action("mark_recovery_successful")

    assert result.new_mode == "recovery_cancelled"
    assert result.state.shutdown_candidate is False
    assert result.state.shutdown_performed is False


def test_apply_threat_level_candidate_reads_tmp_threat_state(tmp_path):
    config = _config_for(tmp_path)
    threat_manager = ThreatManager(config)
    threat_manager.record_event("forced_exit_attempt")
    threat_manager.record_event("serious_follow_up_event")
    manager = ShutdownEscalationManager(config)

    result = manager.perform_action("apply_threat_level_candidate")

    assert result.new_mode == "candidate"
    assert result.state.shutdown_candidate is True
    assert result.state.threat_level_at_last_update == 5
    assert result.state.shutdown_performed is False


def test_apply_protected_mode_candidate_reads_tmp_protected_state(tmp_path):
    config = _config_for(tmp_path)
    threat_manager = ThreatManager(config)
    threat_manager.record_event("forced_exit_attempt")
    threat_manager.record_event("serious_follow_up_event")
    ProtectedModeManager(config).perform_action("apply_threat_recommendation")
    manager = ShutdownEscalationManager(config)

    result = manager.perform_action("apply_protected_mode_candidate")

    assert result.new_mode == "candidate"
    assert result.state.protected_shutdown_candidate is True
    assert result.state.protected_mode_at_last_update == "armed"
    assert result.state.shutdown_performed is False


def test_real_shutdown_flag_blocks_to_safe_config_state(tmp_path):
    manager = ShutdownEscalationManager(_config_for(tmp_path, {"real_shutdown_enabled": True}))

    result = manager.perform_action("mark_shutdown_candidate")

    assert result.success is False
    assert result.status == "blocked"
    assert result.new_mode == "blocked_by_config"
    assert result.state.real_shutdown_enabled is False
    assert result.state.shutdown_performed is False


def test_guard_check_never_schedules_shutdown(tmp_path):
    fake_executor = FakeShutdownExecutor()
    manager = ShutdownEscalationManager(_config_for(tmp_path), executor=fake_executor, platform_name="Windows")

    result = manager.check_real_shutdown_guards()

    assert result.success is True
    assert result.state.guarded_real_shutdown_ready is False
    assert fake_executor.scheduled_countdowns == []


def test_real_shutdown_request_blocks_when_guards_not_ready(tmp_path):
    fake_executor = FakeShutdownExecutor()
    manager = ShutdownEscalationManager(_config_for(tmp_path), executor=fake_executor, platform_name="Windows")

    result = manager.request_guarded_real_shutdown("SHUT DOWN SAFEDESK TEST")

    assert result.success is False
    assert result.status == "blocked"
    assert result.state.real_shutdown_scheduled is False
    assert fake_executor.scheduled_countdowns == []


def test_real_shutdown_request_blocks_when_confirmation_phrase_wrong(tmp_path):
    fake_executor = FakeShutdownExecutor()
    manager = ShutdownEscalationManager(_config_for(tmp_path, real_shutdown=True), executor=fake_executor, platform_name="Windows")

    result = manager.request_guarded_real_shutdown("wrong phrase")

    assert result.success is False
    assert result.status == "blocked"
    assert result.state.real_shutdown_confirmation_matched is False
    assert fake_executor.scheduled_countdowns == []


def test_real_shutdown_request_schedules_only_when_guards_ready_and_phrase_matches(tmp_path):
    fake_executor = FakeShutdownExecutor()
    manager = ShutdownEscalationManager(_config_for(tmp_path, real_shutdown=True), executor=fake_executor, platform_name="Windows")

    result = manager.request_guarded_real_shutdown("SHUT DOWN SAFEDESK TEST")

    assert result.success is True
    assert result.state.guarded_real_shutdown_ready is True
    assert result.state.real_shutdown_confirmation_matched is True
    assert result.state.real_shutdown_requested is True
    assert result.state.real_shutdown_scheduled is True
    assert result.state.shutdown_performed is False
    assert fake_executor.scheduled_countdowns == [(60, "SafeDesk guarded shutdown test")]


def test_abort_pending_real_shutdown_calls_executor(tmp_path):
    fake_executor = FakeShutdownExecutor()
    manager = ShutdownEscalationManager(_config_for(tmp_path, real_shutdown=True), executor=fake_executor, platform_name="Windows")

    result = manager.abort_pending_real_shutdown()

    assert result.success is True
    assert result.state.real_shutdown_abort_requested is True
    assert result.state.real_shutdown_aborted is True
    assert fake_executor.abort_calls == 1


def test_successful_abort_clears_scheduled_real_shutdown_state(tmp_path):
    fake_executor = FakeShutdownExecutor()
    manager = ShutdownEscalationManager(_config_for(tmp_path, real_shutdown=True), executor=fake_executor, platform_name="Windows")

    scheduled = manager.request_guarded_real_shutdown("SHUT DOWN SAFEDESK TEST")
    aborted = manager.abort_pending_real_shutdown()

    assert scheduled.state.real_shutdown_scheduled is True
    assert aborted.state.real_shutdown_abort_requested is True
    assert aborted.state.real_shutdown_aborted is True
    assert aborted.state.real_shutdown_scheduled is False
    assert aborted.state.shutdown_performed is False
    assert fake_executor.abort_calls == 1


def test_full_guarded_real_shutdown_config_preserves_dry_run_actions_without_scheduling(tmp_path):
    fake_executor = FakeShutdownExecutor()
    manager = ShutdownEscalationManager(_config_for(tmp_path, real_shutdown=True), executor=fake_executor, platform_name="Windows")

    result = manager.perform_action("mark_shutdown_candidate")

    assert result.success is True
    assert result.new_mode == "candidate"
    assert result.state.shutdown_candidate is True
    assert result.state.shutdown_performed is False
    assert fake_executor.scheduled_countdowns == []


def test_dry_run_countdown_completion_does_not_schedule_real_shutdown(tmp_path):
    fake_executor = FakeShutdownExecutor()
    manager = ShutdownEscalationManager(_config_for(tmp_path), executor=fake_executor, platform_name="Windows")
    manager.perform_action("mark_shutdown_candidate")
    manager.perform_action("prepare_demo_countdown")
    manager.perform_action("start_demo_countdown")
    manager.perform_action("tick_demo_countdown")
    manager.perform_action("tick_demo_countdown")

    assert fake_executor.scheduled_countdowns == []


def test_threat_and_protected_candidate_actions_do_not_schedule_real_shutdown(tmp_path):
    fake_executor = FakeShutdownExecutor()
    config = _config_for(tmp_path)
    threat_manager = ThreatManager(config)
    threat_manager.record_event("forced_exit_attempt")
    threat_manager.record_event("serious_follow_up_event")
    ProtectedModeManager(config).perform_action("apply_threat_recommendation")
    manager = ShutdownEscalationManager(config, executor=fake_executor, platform_name="Windows")

    manager.perform_action("apply_threat_level_candidate")
    manager.perform_action("apply_protected_mode_candidate")

    assert fake_executor.scheduled_countdowns == []


def test_shutdown_events_log_safe_category_and_false_action_metadata(tmp_path):
    manager = ShutdownEscalationManager(_config_for(tmp_path))

    manager.perform_action("mark_shutdown_candidate")
    events = manager.event_logger.store.list_events()

    assert any(event.category == "shutdown_escalation" for event in events)
    assert all(event.metadata["shutdown_performed"] is False for event in events)
    assert all(event.metadata["restart_performed"] is False for event in events)
    assert all(event.metadata["logoff_performed"] is False for event in events)
    assert all(event.metadata["lockdown_performed"] is False for event in events)
    assert all(event.metadata["alarm_performed"] is False for event in events)
    assert all(event.metadata["email_sent"] is False for event in events)


def test_real_shutdown_event_metadata_does_not_store_phrase_or_command(tmp_path):
    fake_executor = FakeShutdownExecutor()
    manager = ShutdownEscalationManager(_config_for(tmp_path, real_shutdown=True), executor=fake_executor, platform_name="Windows")

    manager.request_guarded_real_shutdown("SHUT DOWN SAFEDESK TEST")
    raw_events = str([event.message + str(event.metadata) for event in manager.event_logger.store.list_events()])

    assert "SHUT DOWN SAFEDESK TEST" not in raw_events
    assert "shutdown /s" not in raw_events.lower()
    assert "SafeDesk guarded shutdown test" not in raw_events
    assert "shutdown_performed': False" in raw_events or '"shutdown_performed": False' in raw_events

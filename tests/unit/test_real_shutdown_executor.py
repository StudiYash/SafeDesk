from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.shutdown_escalation.real_shutdown_executor import RealShutdownExecutor


def test_executor_rejects_non_windows_platform():
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args[0], 0)

    result = RealShutdownExecutor(platform_name="Linux", run_command=fake_run).schedule_windows_shutdown(60)

    assert result.success is False
    assert result.status == "unsupported_platform"
    assert calls == []


def test_executor_rejects_countdown_below_30():
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args[0], 0)

    result = RealShutdownExecutor(platform_name="Windows", run_command=fake_run).schedule_windows_shutdown(10)

    assert result.success is False
    assert result.status == "invalid_countdown"
    assert calls == []


def test_executor_schedules_with_argument_list_and_shell_false():
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args[0], 0)

    result = RealShutdownExecutor(platform_name="Windows", run_command=fake_run).schedule_windows_shutdown(60)

    assert result.success is True
    assert result.status == "scheduled"
    args, kwargs = calls[0]
    assert args[0] == ["shutdown", "/s", "/t", "60", "/c", "SafeDesk guarded shutdown test"]
    assert kwargs["shell"] is False


def test_executor_aborts_with_argument_list_and_shell_false():
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args[0], 0)

    result = RealShutdownExecutor(platform_name="Windows", run_command=fake_run).abort_windows_shutdown()

    assert result.success is True
    assert result.status == "aborted"
    args, kwargs = calls[0]
    assert args[0] == ["shutdown", "/a"]
    assert kwargs["shell"] is False

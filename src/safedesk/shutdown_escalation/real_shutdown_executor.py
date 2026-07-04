"""Windows-only real shutdown executor for guarded manual tests."""

from __future__ import annotations

from dataclasses import dataclass
import platform
import subprocess
from typing import Callable


@dataclass(frozen=True)
class RealShutdownExecutionResult:
    """Safe result from scheduling or aborting a Windows shutdown."""

    success: bool
    status: str
    message: str
    countdown_seconds: int = 0


RunCallable = Callable[..., subprocess.CompletedProcess]


class RealShutdownExecutor:
    """Executor for explicit guarded Windows shutdown actions."""

    def __init__(self, platform_name: str | None = None, run_command: RunCallable | None = None):
        self.platform_name = platform_name or platform.system()
        self.run_command = run_command or subprocess.run

    def schedule_windows_shutdown(
        self,
        countdown_seconds: int,
        comment: str = "SafeDesk guarded shutdown test",
    ) -> RealShutdownExecutionResult:
        """Schedule a Windows shutdown with a delay, using an argument list only."""

        if self.platform_name != "Windows":
            return RealShutdownExecutionResult(False, "unsupported_platform", "Real shutdown is only supported on Windows.")
        if isinstance(countdown_seconds, bool) or not isinstance(countdown_seconds, int) or countdown_seconds < 30:
            return RealShutdownExecutionResult(False, "invalid_countdown", "Real shutdown countdown must be at least 30 seconds.")

        safe_comment = str(comment or "SafeDesk guarded shutdown test")[:256]
        args = ["shutdown", "/s", "/t", str(countdown_seconds), "/c", safe_comment]
        try:
            completed = self.run_command(args, shell=False, check=False, capture_output=True, text=True)
        except Exception:
            return RealShutdownExecutionResult(False, "execution_error", "Windows shutdown command could not be scheduled.")

        if int(getattr(completed, "returncode", 1)) == 0:
            return RealShutdownExecutionResult(
                True,
                "scheduled",
                f"Guarded Windows shutdown was scheduled for {countdown_seconds} seconds from now.",
                countdown_seconds=countdown_seconds,
            )
        return RealShutdownExecutionResult(False, "execution_failed", "Windows shutdown command was not scheduled.")

    def abort_windows_shutdown(self) -> RealShutdownExecutionResult:
        """Abort a pending Windows shutdown, using an argument list only."""

        if self.platform_name != "Windows":
            return RealShutdownExecutionResult(False, "unsupported_platform", "Shutdown abort is only supported on Windows.")

        try:
            completed = self.run_command(["shutdown", "/a"], shell=False, check=False, capture_output=True, text=True)
        except Exception:
            return RealShutdownExecutionResult(False, "execution_error", "Pending Windows shutdown could not be aborted.")

        if int(getattr(completed, "returncode", 1)) == 0:
            return RealShutdownExecutionResult(True, "aborted", "Pending Windows shutdown abort completed.")
        return RealShutdownExecutionResult(False, "abort_failed", "Pending Windows shutdown could not be aborted.")


def schedule_windows_shutdown(
    countdown_seconds: int,
    comment: str = "SafeDesk guarded shutdown test",
    platform_name: str | None = None,
    run_command: RunCallable | None = None,
) -> RealShutdownExecutionResult:
    """Convenience wrapper for scheduling a guarded Windows shutdown."""

    return RealShutdownExecutor(platform_name=platform_name, run_command=run_command).schedule_windows_shutdown(
        countdown_seconds,
        comment,
    )


def abort_windows_shutdown(
    platform_name: str | None = None,
    run_command: RunCallable | None = None,
) -> RealShutdownExecutionResult:
    """Convenience wrapper for aborting a pending guarded Windows shutdown."""

    return RealShutdownExecutor(platform_name=platform_name, run_command=run_command).abort_windows_shutdown()

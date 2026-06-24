"""Lightweight configuration models."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

IssueSeverity = Literal["info", "warning", "error"]


@dataclass(frozen=True)
class EnvironmentSettings:
    """Sanitized environment settings used by configuration validation."""

    safedesk_env: str = "development"
    email_sender_address: str = ""
    email_app_password_present: bool = False
    otp_receiver_email: str = ""
    enable_real_email: bool = False
    enable_real_shutdown: bool = False
    enable_real_lockdown: bool = False
    env_file_loaded: bool = False
    env_file_path: Path | None = None


@dataclass(frozen=True)
class ConfigLoadResult:
    """Result of loading and merging configuration files."""

    config: dict[str, Any]
    loaded_files: tuple[Path, ...] = ()
    local_config_loaded: bool = False


@dataclass(frozen=True)
class ConfigValidationIssue:
    """A validation issue safe to print publicly."""

    severity: IssueSeverity
    code: str
    message: str


@dataclass(frozen=True)
class ConfigValidationReport:
    """Validation report for SafeDesk configuration checks."""

    is_valid: bool
    issues: tuple[ConfigValidationIssue, ...] = ()

    @property
    def errors(self) -> tuple[ConfigValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "error")

    @property
    def warnings(self) -> tuple[ConfigValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "warning")


@dataclass(frozen=True)
class SafeDeskRuntimeSettings:
    """Sanitized runtime settings used by the startup check."""

    app_name: str
    version: str
    environment: str
    security_mode: str
    demo_safe_mode: bool
    real_email_enabled: bool
    real_shutdown_enabled: bool
    real_lockdown_enabled: bool
    validation_report: ConfigValidationReport = field(default_factory=lambda: ConfigValidationReport(True))

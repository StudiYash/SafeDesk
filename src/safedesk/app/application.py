"""Safe application startup layer for SafeDesk."""

from dataclasses import dataclass
from pathlib import Path

from safedesk.config import build_runtime_settings, load_config, load_environment, validate_config
from safedesk.config.models import ConfigLoadResult, ConfigValidationReport, EnvironmentSettings, SafeDeskRuntimeSettings
from safedesk.storage.paths import env_path, project_root as default_project_root


@dataclass(frozen=True)
class RuntimeContext:
    project_root: Path
    env: EnvironmentSettings
    load_result: ConfigLoadResult
    report: ConfigValidationReport
    settings: SafeDeskRuntimeSettings


def _format_bool(value: bool) -> str:
    return "true" if value else "false"


def load_runtime_context(root: Path | None = None) -> RuntimeContext:
    runtime_root = (root or default_project_root()).resolve()
    env = load_environment(env_file=env_path(runtime_root))
    load_result = load_config(root=runtime_root)
    report = validate_config(load_result.config, env, root=runtime_root)
    settings = build_runtime_settings(load_result.config, env, report)
    return RuntimeContext(
        project_root=runtime_root,
        env=env,
        load_result=load_result,
        report=report,
        settings=settings,
    )


def print_configuration_summary(settings: SafeDeskRuntimeSettings, report: ConfigValidationReport) -> None:
    print("SafeDesk v1 Configuration Check")
    print(f"Application: {settings.app_name} {settings.version}")
    print(f"Environment: {settings.environment}")
    print(f"Security mode: {settings.security_mode}")
    print(f"Demo/safe mode: {'enabled' if settings.demo_safe_mode else 'disabled'}")
    print(f"Real email enabled: {_format_bool(settings.real_email_enabled)}")
    print(f"Real shutdown enabled: {_format_bool(settings.real_shutdown_enabled)}")
    print(f"Real lockdown enabled: {_format_bool(settings.real_lockdown_enabled)}")

    for issue in report.issues:
        print(f"{issue.severity.upper()}: {issue.message}")

    if report.is_valid:
        print("Configuration status: ready for safe development mode")
    else:
        print("Configuration status: review required before SafeDesk can continue")


def run_config_check(root: Path | None = None) -> int:
    context = load_runtime_context(root=root)
    print_configuration_summary(context.settings, context.report)
    return 0 if context.report.is_valid else 1


def run_gui_app(root: Path | None = None) -> int:
    context = load_runtime_context(root=root)
    if not context.report.is_valid:
        print_configuration_summary(context.settings, context.report)
        return 1

    try:
        from safedesk.gui.main_window import SafeDeskMainWindow
    except ModuleNotFoundError as exc:
        if exc.name == "customtkinter":
            print("SafeDesk GUI dependency missing: customtkinter")
            print("Install Phase 4 requirements before launching the GUI shell.")
            return 1
        raise

    app = SafeDeskMainWindow(context)
    app.mainloop()
    return 0


def run_app(check_config_only: bool = False, root: Path | None = None) -> int:
    if check_config_only:
        return run_config_check(root=root)
    return run_gui_app(root=root)

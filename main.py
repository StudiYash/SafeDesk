from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from safedesk.config import build_runtime_settings, load_config, load_environment, validate_config


def _format_bool(value: bool) -> str:
    return "true" if value else "false"


def main() -> int:
    print("SafeDesk v1 Configuration Check")

    env = load_environment()
    load_result = load_config()
    report = validate_config(load_result.config, env)
    settings = build_runtime_settings(load_result.config, env, report)

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
        return 0

    print("Configuration status: review required before SafeDesk can continue")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

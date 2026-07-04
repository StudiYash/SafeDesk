from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.shutdown_escalation.shutdown_guard import evaluate_shutdown_guards


def _guarded_config():
    return deep_merge(
        DEFAULT_CONFIG,
        {
            "feature_flags": {"enable_real_shutdown": True},
            "app": {"demo_safe_mode": False},
            "security_mode": {"default_mode": "standard"},
            "shutdown": {
                "allow_guarded_real_shutdown": True,
                "real_shutdown_enabled": True,
                "real_shutdown_command_enabled": True,
                "demo_shutdown_only": False,
                "require_manual_confirmation": True,
                "real_shutdown_requires_confirmation_phrase": True,
                "real_shutdown_confirmation_phrase": "SHUT DOWN SAFEDESK TEST",
                "real_shutdown_countdown_seconds": 60,
                "allow_abort_real_shutdown": True,
            },
        },
    )


def test_shutdown_guard_report_is_not_ready_by_default():
    report = evaluate_shutdown_guards(DEFAULT_CONFIG, platform_name="Windows")

    assert report.ready is False
    assert report.platform_supported is True
    assert any(check.name == "feature_flag_enabled" and check.passed is False for check in report.checks)


def test_shutdown_guard_report_ready_only_with_all_guards_on_windows():
    report = evaluate_shutdown_guards(_guarded_config(), platform_name="Windows")

    assert report.ready is True
    assert report.platform_supported is True
    assert all(check.passed for check in report.checks)


def test_shutdown_guard_report_blocks_unsupported_platform():
    report = evaluate_shutdown_guards(_guarded_config(), platform_name="Linux")

    assert report.ready is False
    assert report.platform_supported is False
    assert any(check.name == "platform_supported" and check.passed is False for check in report.checks)

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.developer_tools import DeveloperToolsPolicy


def _status(overrides):
    return DeveloperToolsPolicy(deep_merge(DEFAULT_CONFIG, overrides)).build_status()


def test_default_policy_allows_landing_demo_routes_and_diagnostics():
    status = DeveloperToolsPolicy(DEFAULT_CONFIG).build_status()

    assert status.landing_visible is True
    assert status.demo_routes_allowed is True
    assert status.diagnostics_visible is True


def test_effective_runtime_environment_is_authoritative():
    production = DeveloperToolsPolicy(
        DEFAULT_CONFIG,
        effective_environment="production",
    ).build_status()
    development = DeveloperToolsPolicy(
        DEFAULT_CONFIG,
        effective_environment="development",
    ).build_status()

    assert production.environment_supported is False
    assert production.landing_visible is False
    assert production.demo_routes_allowed is False
    assert production.diagnostics_visible is False
    assert development.environment_supported is True
    assert development.landing_visible is True
    assert development.demo_routes_allowed is True
    assert development.diagnostics_visible is True


def test_each_foundation_guard_can_hide_developer_tools():
    cases = (
        {"app": {"environment": "production"}},
        {"app": {"demo_safe_mode": False}},
        {"security_mode": {"default_mode": "standard"}},
        {"developer_tools": {"enabled": False}},
        {"developer_tools": {"demo_only": False}},
    )
    for override in cases:
        status = _status(override)
        assert status.landing_visible is False
        assert status.demo_routes_allowed is False
        assert status.diagnostics_visible is False
        assert "path" not in status.safe_message.lower()
        assert "secret" not in status.safe_message.lower()


def test_landing_visibility_demo_route_and_diagnostics_flags_are_independent():
    diagnostics_only = _status({"developer_tools": {"show_demo_screens": False}})
    demos_only = _status({"developer_tools": {"show_runtime_diagnostics": False}})
    hidden = _status(
        {"developer_tools": {"show_demo_screens": False, "show_runtime_diagnostics": False}}
    )

    assert diagnostics_only.landing_visible and not diagnostics_only.demo_routes_allowed
    assert diagnostics_only.diagnostics_visible
    assert demos_only.landing_visible and demos_only.demo_routes_allowed
    assert not demos_only.diagnostics_visible
    assert hidden.landing_visible is False

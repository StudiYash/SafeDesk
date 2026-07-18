from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from safedesk.config.config_loader import deep_merge
from safedesk.config.defaults import DEFAULT_CONFIG
from safedesk.gui.navigation import (
    ABOUT,
    ALARM_SYSTEM,
    AUTHENTICATION_SETUP,
    DASHBOARD,
    DEVELOPER_ROUTE_NAMES,
    DEVELOPER_TOOLS,
    EVENT_LOGS,
    HOME,
    INTRUDER_HISTORY,
    OWNER_FACE_REGISTRATION,
    SCREEN_NAMES,
    SETTINGS,
    SETUP_STATUS,
    admin_route_allowed,
    visible_sidebar_sections,
)


def test_normal_sidebar_is_grouped_and_contains_no_individual_demo_routes():
    sections = visible_sidebar_sections(DEFAULT_CONFIG)
    lookup = {name: tuple(screen.name for screen in screens) for name, screens in sections}

    assert lookup["Overview"] == (HOME, DASHBOARD)
    assert lookup["Owner & Setup"] == (SETUP_STATUS, OWNER_FACE_REGISTRATION, AUTHENTICATION_SETUP)
    assert lookup["Security Activity"] == (EVENT_LOGS, INTRUDER_HISTORY, ALARM_SYSTEM)
    assert lookup["Developer"] == (DEVELOPER_TOOLS,)
    assert lookup["System"] == (SETTINGS, ABOUT)
    visible_names = {name for screens in lookup.values() for name in screens}
    assert visible_names.isdisjoint(DEVELOPER_ROUTE_NAMES)
    assert DEVELOPER_ROUTE_NAMES.issubset(SCREEN_NAMES)


def test_developer_landing_visibility_uses_policy():
    config = deep_merge(
        DEFAULT_CONFIG,
        {"developer_tools": {"show_demo_screens": False, "show_runtime_diagnostics": False}},
    )
    visible = {screen.name for _, screens in visible_sidebar_sections(config) for screen in screens}
    assert DEVELOPER_TOOLS not in visible


def test_direct_developer_routes_are_guarded_independently_of_sidebar_visibility():
    demo_route = next(iter(DEVELOPER_ROUTE_NAMES))
    assert admin_route_allowed(DEFAULT_CONFIG, demo_route) is True
    assert admin_route_allowed(DEFAULT_CONFIG, DEVELOPER_TOOLS) is True
    assert admin_route_allowed(DEFAULT_CONFIG, HOME) is True

    blocked = deep_merge(DEFAULT_CONFIG, {"developer_tools": {"show_demo_screens": False}})
    assert admin_route_allowed(blocked, demo_route) is False
    assert admin_route_allowed(blocked, DEVELOPER_TOOLS) is True

    hidden = deep_merge(
        DEFAULT_CONFIG,
        {"developer_tools": {"show_demo_screens": False, "show_runtime_diagnostics": False}},
    )
    assert admin_route_allowed(hidden, demo_route) is False
    assert admin_route_allowed(hidden, DEVELOPER_TOOLS) is False
    assert admin_route_allowed(hidden, "unknown_route") is False


def test_production_effective_environment_hides_and_blocks_all_developer_routes():
    visible = {
        screen.name
        for _, screens in visible_sidebar_sections(
            DEFAULT_CONFIG,
            effective_environment="production",
        )
        for screen in screens
    }

    assert DEVELOPER_TOOLS not in visible
    assert admin_route_allowed(
        DEFAULT_CONFIG,
        DEVELOPER_TOOLS,
        effective_environment="production",
    ) is False
    for route in DEVELOPER_ROUTE_NAMES:
        assert admin_route_allowed(
            DEFAULT_CONFIG,
            route,
            effective_environment="production",
        ) is False
    assert admin_route_allowed(
        DEFAULT_CONFIG,
        HOME,
        effective_environment="production",
    ) is True
    assert admin_route_allowed(
        DEFAULT_CONFIG,
        SETTINGS,
        effective_environment="production",
    ) is True


def test_main_window_has_factories_grouping_route_guard_and_owner_gate():
    source = (SRC / "safedesk" / "gui" / "main_window.py").read_text(encoding="utf-8")

    assert "visible_sidebar_sections(" in source
    assert "effective_environment=self.effective_environment" in source
    assert "DEVELOPER_TOOLS: lambda" in source
    assert "SETTINGS: SettingsScreen" in source
    assert "_guard_admin_screen_route" in source
    assert "self.show_admin_gate(screen_name)" in source
    assert "StartupMaximizeController(" in source
    assert "requested=self._startup_maximize_requested" in source
    assert "self.startup_maximize_controller.arm()" in source
    assert "self.startup_maximize_controller.cancel()" in source
    assert "self.after_idle(self._apply_start_maximized)" not in source
    assert "self.project_root = context.project_root" in source
    assert "_resume_current_screen_resources" in source

"""Safe models for Developer Tools policy and diagnostics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeveloperToolsStatus:
    environment_supported: bool
    demo_safe_mode: bool
    security_mode_supported: bool
    foundation_enabled: bool
    demo_only: bool
    show_demo_screens: bool
    show_runtime_diagnostics: bool
    landing_visible: bool
    demo_routes_allowed: bool
    diagnostics_visible: bool
    safe_message: str


@dataclass(frozen=True)
class DeveloperDiagnostic:
    label: str
    value: str


@dataclass(frozen=True)
class DeveloperDiagnosticsSummary:
    items: tuple[DeveloperDiagnostic, ...]
    message: str

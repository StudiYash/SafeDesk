"""Models for SafeDesk owner dashboard summaries."""

from __future__ import annotations

from dataclasses import dataclass

from safedesk.intruder_history import IntruderHistorySummary


@dataclass(frozen=True)
class DashboardRow:
    label: str
    value: str


@dataclass(frozen=True)
class DashboardSection:
    title: str
    rows: tuple[DashboardRow, ...]
    accent: str = ""


@dataclass(frozen=True)
class DashboardEventSummary:
    event_number: int
    timestamp: str
    category: str
    action: str
    status: str
    severity: str
    message: str


@dataclass(frozen=True)
class DashboardSummary:
    sections: tuple[DashboardSection, ...]
    recent_events: tuple[DashboardEventSummary, ...]
    intruder_history: IntruderHistorySummary

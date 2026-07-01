"""Pure helpers for displaying and filtering local SafeDesk events."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Iterable

from safedesk.logging.log_models import SafeDeskEvent

ALL_FILTER = "All"
SORT_FIELDS = (
    "Event Number",
    "Timestamp",
    "Category",
    "Action",
    "Status",
    "Severity",
    "Source",
    "Message",
)
SORT_DIRECTIONS = ("Ascending", "Descending")


def format_event_timestamp_for_display(timestamp: str) -> str:
    """Return a local-time display timestamp without exposing raw parser errors."""

    try:
        normalized = str(timestamp).strip()
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone().strftime("%Y-%m-%d-%H-%M-%S")
    except Exception:
        return "invalid timestamp"


def build_filter_options(events: Iterable[SafeDeskEvent]) -> dict[str, list[str]]:
    """Return filter option lists discovered from current events."""

    event_list = list(events)
    return {
        "category": _unique_options(event.category for event in event_list),
        "status": _unique_options(event.status for event in event_list),
        "severity": _unique_options(event.severity for event in event_list),
        "action": _unique_options(event.action for event in event_list),
        "source": _unique_options(event.source for event in event_list),
    }


def apply_event_filters(events: Iterable[SafeDeskEvent], filters: dict[str, str] | None) -> list[SafeDeskEvent]:
    """Apply category/status/severity/action/source filters before search."""

    active_filters = filters or {}
    filtered = list(events)
    for field in ("category", "status", "severity", "action", "source"):
        selected = active_filters.get(field, ALL_FILTER)
        if selected and selected != ALL_FILTER:
            filtered = [event for event in filtered if str(getattr(event, field)) == selected]
    return filtered


def event_matches_search(event: SafeDeskEvent, query: str) -> bool:
    """Return whether the event matches a case-insensitive dashboard search."""

    normalized_query = query.strip().lower()
    if not normalized_query:
        return True

    metadata_text = json.dumps(event.metadata, sort_keys=True)
    searchable = " ".join(
        [
            str(event.event_number),
            event.timestamp,
            format_event_timestamp_for_display(event.timestamp),
            event.category,
            event.action,
            event.status,
            event.severity,
            event.message,
            event.source,
            metadata_text,
        ]
    ).lower()
    return normalized_query in searchable


def apply_event_search(events: Iterable[SafeDeskEvent], query: str) -> list[SafeDeskEvent]:
    """Apply dashboard search after filters."""

    return [event for event in events if event_matches_search(event, query)]


def sort_events(events: Iterable[SafeDeskEvent], sort_field: str = "Event Number", direction: str = "Ascending") -> list[SafeDeskEvent]:
    """Sort events for display without changing stable event numbers."""

    reverse = direction == "Descending"
    key_name = sort_field if sort_field in SORT_FIELDS else "Event Number"

    def sort_key(event: SafeDeskEvent):
        if key_name == "Event Number":
            return (event.event_number, event.event_number)
        if key_name == "Timestamp":
            return (event.timestamp, event.event_number)
        if key_name == "Category":
            return (event.category.lower(), event.event_number)
        if key_name == "Action":
            return (event.action.lower(), event.event_number)
        if key_name == "Status":
            return (event.status.lower(), event.event_number)
        if key_name == "Severity":
            return (event.severity.lower(), event.event_number)
        if key_name == "Source":
            return (event.source.lower(), event.event_number)
        if key_name == "Message":
            return (event.message.lower(), event.event_number)
        return (event.event_number, event.event_number)

    return sorted(list(events), key=sort_key, reverse=reverse)


def filter_search_sort_events(
    events: Iterable[SafeDeskEvent],
    filters: dict[str, str] | None = None,
    query: str = "",
    sort_field: str = "Event Number",
    direction: str = "Ascending",
) -> list[SafeDeskEvent]:
    """Apply filters, then search, then display sorting."""

    filtered = apply_event_filters(events, filters)
    searched = apply_event_search(filtered, query)
    return sort_events(searched, sort_field, direction)


def _unique_options(values: Iterable[str]) -> list[str]:
    unique = sorted({str(value) for value in values if str(value)})
    return [ALL_FILTER, *unique]

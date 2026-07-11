"""Safe local intruder evidence manifest reader."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from safedesk.intruder_history.intruder_history_models import (
    IntruderEvidenceItem,
    IntruderHistorySummary,
)
from safedesk.storage.paths import project_root

VALID_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
LOCAL_PATH_PLACEHOLDER = "[local path hidden]"
WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r"(?i)\b[a-z]:[\\/][^\s,;|<>\"']+")
HOME_PATH_PATTERN = re.compile(r"(?i)(?<![\w.-])(?:~[\\/][^\s,;|<>\"']+|[\\/](?:Users|home)[\\/][^\s,;|<>\"']+)")
PROJECT_DATA_PATH_PATTERN = re.compile(
    r"(?i)(?<![\w.-])data[\\/](?:intruders|config|owner|logs|cache)(?:[\\/][^\s,;|<>\"']*)?"
)


class IntruderHistoryReader:
    """Read ignored local intruder evidence records without exposing private paths."""

    def __init__(self, config: dict, root: Path | None = None):
        self.config = config
        self.root = root or project_root()
        self.intruder_config = config.get("intruder_detection", {}) if isinstance(config, dict) else {}
        self.manifest_path = self._resolve_path(self.intruder_config.get("manifest_path", "data/config/intruder_capture_manifest.json"))
        self.images_dir = self._resolve_path(self.intruder_config.get("intruder_images_dir", "data/intruders"))

    def build_summary(self, limit: int | None = None) -> IntruderHistorySummary:
        items = self.list_items(limit=limit)
        image_available_count = sum(1 for item in items if item.image_available)
        most_recent = items[0].captured_at if items else "No captures"
        message = f"{len(items)} evidence item(s) loaded." if items else "No intruder evidence captured yet."
        return IntruderHistorySummary(
            total_count=len(items),
            image_available_count=image_available_count,
            most_recent_capture=most_recent,
            items=tuple(items),
            message=message,
        )

    def list_items(self, limit: int | None = None) -> tuple[IntruderEvidenceItem, ...]:
        records = self._load_manifest_records()
        items: list[IntruderEvidenceItem] = []
        for index, record in enumerate(records, start=1):
            item = self._item_from_record(record, index)
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: item.captured_at, reverse=True)
        if limit is not None:
            return tuple(items[: max(0, int(limit))])
        return tuple(items)

    def _load_manifest_records(self) -> list[dict[str, Any]]:
        if not self.manifest_path.exists():
            return []
        try:
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return []

        if isinstance(payload, list):
            raw_records = payload
        elif isinstance(payload, dict):
            raw_records = payload.get("captures", payload.get("records", payload.get("evidence", [])))
        else:
            raw_records = []
        if not isinstance(raw_records, list):
            return []
        return [record for record in raw_records if isinstance(record, dict)]

    def _item_from_record(self, record: dict[str, Any], index: int) -> IntruderEvidenceItem | None:
        capture_id = self._safe_text(record.get("capture_id") or record.get("id") or f"capture-{index}", limit=80)
        if not capture_id:
            return None
        captured_at = self._safe_text(
            record.get("created_at") or record.get("captured_at") or record.get("timestamp") or "Unknown time",
            limit=80,
        )
        status = self._safe_text(
            record.get("result_status") or record.get("status") or record.get("classification") or record.get("result") or "captured",
            limit=80,
        )
        safe_message = self._safe_text(record.get("reason") or record.get("message") or "Local evidence capture.", limit=160)
        event_reference = self._safe_text(record.get("event_number") or record.get("event_id") or "", limit=80)
        preview_path = self._resolve_preview_path(record)
        image_available = preview_path is not None and preview_path.exists()
        return IntruderEvidenceItem(
            capture_id=capture_id,
            captured_at=captured_at,
            status=status,
            safe_message=safe_message,
            image_available=image_available,
            preview_allowed=image_available,
            event_reference=event_reference,
            preview_path=preview_path if image_available else None,
        )

    def _resolve_preview_path(self, record: dict[str, Any]) -> Path | None:
        raw_value = (
            record.get("relative_image_path")
            or record.get("image_filename")
            or record.get("image_path")
            or record.get("path")
            or record.get("file")
        )
        if not isinstance(raw_value, str) or not raw_value.strip():
            return None
        raw_path = Path(raw_value)
        candidate = raw_path if raw_path.is_absolute() else self.images_dir / raw_path
        try:
            resolved_dir = self.images_dir.resolve(strict=False)
            resolved_candidate = candidate.resolve(strict=False)
        except Exception:
            return None
        if not self._is_inside_directory(resolved_candidate, resolved_dir):
            return None
        if resolved_candidate.suffix.lower() not in VALID_IMAGE_SUFFIXES:
            return None
        return resolved_candidate

    def _resolve_path(self, value: Any) -> Path:
        path = Path(str(value))
        return path if path.is_absolute() else self.root / path

    @staticmethod
    def _is_inside_directory(candidate: Path, directory: Path) -> bool:
        try:
            candidate.relative_to(directory)
            return True
        except ValueError:
            return False

    @staticmethod
    def _safe_text(value: Any, limit: int) -> str:
        text = str(value or "").replace("\n", " ").replace("\r", " ").strip()
        text = IntruderHistoryReader._hide_local_paths(text)
        return text[:limit]

    @staticmethod
    def _hide_local_paths(text: str) -> str:
        for pattern in (WINDOWS_ABSOLUTE_PATH_PATTERN, HOME_PATH_PATTERN, PROJECT_DATA_PATH_PATTERN):
            text = pattern.sub(LOCAL_PATH_PLACEHOLDER, text)
        return text

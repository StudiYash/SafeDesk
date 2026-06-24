"""Small reusable status result model."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StatusResult:
    """Simple status payload for safe user-facing checks."""

    status: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status.lower() in {"ok", "ready", "success"}

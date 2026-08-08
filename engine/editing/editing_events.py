from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class EditingEvent:
    """Immutable editing framework event."""

    name: str
    session_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class EditingEvents:
    """Synchronous event bus for editing framework notifications."""

    def __init__(self) -> None:
        """Create an empty editing event bus."""

        self._listeners: dict[str, list] = {}

    def subscribe(self, event_name: str, callback) -> None:
        """Subscribe to an editing event name."""

        listeners = self._listeners.setdefault(event_name, [])
        if callback not in listeners:
            listeners.append(callback)

    def emit(
        self,
        event_name: str,
        session_id: str,
        payload: dict[str, Any] | None = None,
    ) -> EditingEvent:
        """Emit an editing event."""

        event = EditingEvent(event_name, session_id, dict(payload or {}))
        for callback in tuple(self._listeners.get(event_name, [])):
            callback(event)
        for callback in tuple(self._listeners.get("*", [])):
            callback(event)
        return event

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class SnappingEvent:
    """Immutable snapping event."""

    name: str
    session_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class SnappingEvents:
    """Synchronous event bus for snapping notifications."""

    def __init__(self) -> None:
        """Create an empty snapping event bus."""

        self._listeners: dict[str, list[Callable[[SnappingEvent], None]]] = {}

    def subscribe(
        self,
        event_name: str,
        callback: Callable[[SnappingEvent], None],
    ) -> None:
        """Subscribe to a snapping event."""

        listeners = self._listeners.setdefault(event_name, [])
        if callback not in listeners:
            listeners.append(callback)

    def unsubscribe(
        self,
        event_name: str,
        callback: Callable[[SnappingEvent], None],
    ) -> None:
        """Remove a snapping event subscription if present."""

        listeners = self._listeners.get(event_name, [])
        if callback in listeners:
            listeners.remove(callback)

    def emit(
        self,
        event_name: str,
        session_id: str = "",
        payload: dict[str, Any] | None = None,
    ) -> SnappingEvent:
        """Emit one snapping event."""

        event = SnappingEvent(event_name, session_id, dict(payload or {}))
        for callback in tuple(self._listeners.get(event_name, [])):
            callback(event)
        for callback in tuple(self._listeners.get("*", [])):
            callback(event)
        return event

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class HistoryEvent:
    """Immutable history framework event."""

    name: str
    node_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class HistoryEvents:
    """Synchronous event bus for feature history changes."""

    def __init__(self) -> None:
        """Create an empty history event bus."""

        self._listeners: dict[str, list[Callable[[HistoryEvent], None]]] = {}

    def subscribe(
        self,
        event_name: str,
        callback: Callable[[HistoryEvent], None],
    ) -> None:
        """Subscribe to a history event name."""

        listeners = self._listeners.setdefault(event_name, [])
        if callback not in listeners:
            listeners.append(callback)

    def emit(
        self,
        event_name: str,
        node_id: str,
        payload: dict[str, Any] | None = None,
    ) -> HistoryEvent:
        """Emit one history event."""

        event = HistoryEvent(event_name, node_id, dict(payload or {}))
        for callback in tuple(self._listeners.get(event_name, [])):
            callback(event)
        for callback in tuple(self._listeners.get("*", [])):
            callback(event)
        return event

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class TopologyEvent:
    """Immutable topology framework event."""

    name: str
    topology_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class TopologyEvents:
    """Synchronous event bus for topology framework notifications."""

    def __init__(self) -> None:
        """Create an empty topology event bus."""

        self._listeners: dict[str, list[Callable[[TopologyEvent], None]]] = {}

    def subscribe(
        self,
        event_name: str,
        callback: Callable[[TopologyEvent], None],
    ) -> None:
        """Subscribe a callback to topology events."""

        listeners = self._listeners.setdefault(event_name, [])
        if callback not in listeners:
            listeners.append(callback)

    def emit(
        self,
        event_name: str,
        topology_id: str,
        payload: dict[str, Any] | None = None,
    ) -> TopologyEvent:
        """Emit one topology event."""

        event = TopologyEvent(event_name, topology_id, dict(payload or {}))
        for callback in tuple(self._listeners.get(event_name, [])):
            callback(event)
        for callback in tuple(self._listeners.get("*", [])):
            callback(event)
        return event

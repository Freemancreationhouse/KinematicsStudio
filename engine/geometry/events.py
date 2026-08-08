from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class GeometryEvent:
    """Immutable event emitted by the geometry framework."""

    name: str
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class GeometryEvents:
    """Small synchronous event bus for geometry framework notifications."""

    def __init__(self) -> None:
        """Create an empty geometry event bus."""

        self._listeners: dict[str, list[Callable[[GeometryEvent], None]]] = {}
        self._history: list[GeometryEvent] = []

    def subscribe(
        self,
        event_name: str,
        callback: Callable[[GeometryEvent], None],
    ) -> None:
        """Subscribe a callback to one event name."""

        listeners = self._listeners.setdefault(event_name, [])
        if callback not in listeners:
            listeners.append(callback)

    def unsubscribe(
        self,
        event_name: str,
        callback: Callable[[GeometryEvent], None],
    ) -> None:
        """Remove a callback from one event name."""

        listeners = self._listeners.get(event_name, [])
        if callback in listeners:
            listeners.remove(callback)

    def emit(
        self,
        event_name: str,
        *,
        source: str,
        payload: dict[str, Any] | None = None,
    ) -> GeometryEvent:
        """Create, store and dispatch one geometry event."""

        event = GeometryEvent(event_name, source, dict(payload or {}))
        self._history.append(event)
        for callback in tuple(self._listeners.get(event_name, [])):
            callback(event)
        for callback in tuple(self._listeners.get("*", [])):
            callback(event)
        return event

    def history(self) -> tuple[GeometryEvent, ...]:
        """Return emitted events for diagnostics and integration tests."""

        return tuple(self._history)

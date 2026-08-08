from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ScaleEvent:
    """Immutable scale tool event."""

    name: str
    session_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ScaleEvents:
    """Synchronous event bus for scale tool notifications."""

    def __init__(self) -> None:
        """Create an empty scale event bus."""

        self._listeners: dict[str, list[Callable[[ScaleEvent], None]]] = {}

    def subscribe(
        self,
        event_name: str,
        callback: Callable[[ScaleEvent], None],
    ) -> None:
        """Subscribe to a scale event name."""

        listeners = self._listeners.setdefault(event_name, [])
        if callback not in listeners:
            listeners.append(callback)

    def unsubscribe(
        self,
        event_name: str,
        callback: Callable[[ScaleEvent], None],
    ) -> None:
        """Remove a scale event subscription if present."""

        listeners = self._listeners.get(event_name, [])
        if callback in listeners:
            listeners.remove(callback)

    def emit(
        self,
        event_name: str,
        session_id: str,
        payload: dict[str, Any] | None = None,
    ) -> ScaleEvent:
        """Emit one scale event."""

        event = ScaleEvent(event_name, session_id, dict(payload or {}))
        for callback in tuple(self._listeners.get(event_name, [])):
            callback(event)
        for callback in tuple(self._listeners.get("*", [])):
            callback(event)
        return event

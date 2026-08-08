from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class TransformEvent:
    """Immutable transform framework event."""

    name: str
    session_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class TransformEvents:
    """Synchronous event bus for transform framework notifications."""

    def __init__(self) -> None:
        """Create an empty transform event bus."""

        self._listeners: dict[str, list[Callable[[TransformEvent], None]]] = {}

    def subscribe(
        self,
        event_name: str,
        callback: Callable[[TransformEvent], None],
    ) -> None:
        """Subscribe to a transform event name."""

        listeners = self._listeners.setdefault(event_name, [])
        if callback not in listeners:
            listeners.append(callback)

    def unsubscribe(
        self,
        event_name: str,
        callback: Callable[[TransformEvent], None],
    ) -> None:
        """Remove a transform event subscription if present."""

        listeners = self._listeners.get(event_name, [])
        if callback in listeners:
            listeners.remove(callback)

    def emit(
        self,
        event_name: str,
        session_id: str,
        payload: dict[str, Any] | None = None,
    ) -> TransformEvent:
        """Emit one transform event."""

        event = TransformEvent(event_name, session_id, dict(payload or {}))
        for callback in tuple(self._listeners.get(event_name, [])):
            callback(event)
        for callback in tuple(self._listeners.get("*", [])):
            callback(event)
        return event

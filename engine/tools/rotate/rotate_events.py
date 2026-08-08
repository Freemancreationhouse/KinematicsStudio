from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class RotateEvent:
    """Immutable rotate tool event."""

    name: str
    session_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class RotateEvents:
    """Synchronous event bus for rotate tool notifications."""

    def __init__(self) -> None:
        """Create an empty rotate event bus."""

        self._listeners: dict[str, list[Callable[[RotateEvent], None]]] = {}

    def subscribe(
        self,
        event_name: str,
        callback: Callable[[RotateEvent], None],
    ) -> None:
        """Subscribe to a rotate event name."""

        listeners = self._listeners.setdefault(event_name, [])
        if callback not in listeners:
            listeners.append(callback)

    def unsubscribe(
        self,
        event_name: str,
        callback: Callable[[RotateEvent], None],
    ) -> None:
        """Remove a rotate event subscription if present."""

        listeners = self._listeners.get(event_name, [])
        if callback in listeners:
            listeners.remove(callback)

    def emit(
        self,
        event_name: str,
        session_id: str,
        payload: dict[str, Any] | None = None,
    ) -> RotateEvent:
        """Emit one rotate event."""

        event = RotateEvent(event_name, session_id, dict(payload or {}))
        for callback in tuple(self._listeners.get(event_name, [])):
            callback(event)
        for callback in tuple(self._listeners.get("*", [])):
            callback(event)
        return event

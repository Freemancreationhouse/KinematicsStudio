from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class MoveEvent:
    """Immutable Move Tool event."""

    name: str
    session_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class MoveEvents:
    """Synchronous event bus for move tool lifecycle notifications."""

    def __init__(self) -> None:
        """Create an empty move event bus."""

        self._listeners: dict[str, list[Callable[[MoveEvent], None]]] = {}

    def subscribe(
        self,
        event_name: str,
        callback: Callable[[MoveEvent], None],
    ) -> None:
        """Subscribe to a move event."""

        listeners = self._listeners.setdefault(event_name, [])
        if callback not in listeners:
            listeners.append(callback)

    def emit(
        self,
        event_name: str,
        session_id: str,
        payload: dict[str, Any] | None = None,
    ) -> MoveEvent:
        """Emit a move lifecycle event."""

        event = MoveEvent(event_name, session_id, dict(payload or {}))
        for callback in tuple(self._listeners.get(event_name, [])):
            callback(event)
        for callback in tuple(self._listeners.get("*", [])):
            callback(event)
        return event

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


GizmoCallback = Callable[["GizmoEvent"], None]


@dataclass(frozen=True)
class GizmoEvent:
    """Event emitted by the transform gizmo controller."""

    name: str
    session_id: str
    payload: dict[str, Any] = field(default_factory=dict)


class GizmoEvents:
    """Small event dispatcher for gizmo lifecycle and interaction events."""

    def __init__(self) -> None:
        """Create an empty dispatcher."""

        self._listeners: dict[str, list[GizmoCallback]] = defaultdict(list)

    def subscribe(self, name: str, callback: GizmoCallback) -> None:
        """Subscribe to a gizmo event name."""

        listeners = self._listeners[str(name)]
        if callback not in listeners:
            listeners.append(callback)

    def unsubscribe(self, name: str, callback: GizmoCallback) -> None:
        """Unsubscribe from a gizmo event name."""

        listeners = self._listeners.get(str(name))
        if not listeners:
            return
        if callback in listeners:
            listeners.remove(callback)

    def emit(
        self,
        name: str,
        session_id: str = "",
        payload: dict[str, Any] | None = None,
    ) -> GizmoEvent:
        """Emit a gizmo event."""

        event = GizmoEvent(str(name), str(session_id), dict(payload or {}))
        for callback in tuple(self._listeners.get(event.name, ())):
            callback(event)
        for callback in tuple(self._listeners.get("*", ())):
            callback(event)
        return event

    def clear(self) -> None:
        """Remove all event listeners."""

        self._listeners.clear()

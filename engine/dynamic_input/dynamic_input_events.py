from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


DynamicInputCallback = Callable[["DynamicInputEvent"], None]


@dataclass(frozen=True)
class DynamicInputEvent:
    """Event emitted by the dynamic input system."""

    name: str
    session_id: str
    payload: dict[str, Any] = field(default_factory=dict)


class DynamicInputEvents:
    """Small event dispatcher for engine-level HUD coordination."""

    def __init__(self) -> None:
        """Create an empty event dispatcher."""

        self._listeners: dict[str, list[DynamicInputCallback]] = defaultdict(list)

    def subscribe(self, name: str, callback: DynamicInputCallback) -> None:
        """Subscribe a callback to an event name."""

        listeners = self._listeners[str(name)]
        if callback not in listeners:
            listeners.append(callback)

    def unsubscribe(self, name: str, callback: DynamicInputCallback) -> None:
        """Remove a callback from an event name."""

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
    ) -> DynamicInputEvent:
        """Emit an event to named and wildcard listeners."""

        event = DynamicInputEvent(str(name), str(session_id), dict(payload or {}))
        for callback in tuple(self._listeners.get(event.name, ())):
            callback(event)
        for callback in tuple(self._listeners.get("*", ())):
            callback(event)
        return event

    def clear(self) -> None:
        """Remove all event subscriptions."""

        self._listeners.clear()

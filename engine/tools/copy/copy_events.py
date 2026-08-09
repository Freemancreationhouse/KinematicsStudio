from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


CopyCallback = Callable[["CopyEvent"], None]


@dataclass(frozen=True)
class CopyEvent:
    """Event emitted by the professional Copy Tool."""

    name: str
    session_id: str
    payload: dict[str, Any] = field(default_factory=dict)


class CopyEvents:
    """Lightweight event dispatcher for copy session lifecycle."""

    def __init__(self) -> None:
        """Create an empty copy event dispatcher."""

        self._listeners: dict[str, list[CopyCallback]] = defaultdict(list)

    def subscribe(self, name: str, callback: CopyCallback) -> None:
        """Subscribe a callback to a copy event."""

        listeners = self._listeners[str(name)]
        if callback not in listeners:
            listeners.append(callback)

    def unsubscribe(self, name: str, callback: CopyCallback) -> None:
        """Remove a callback from a copy event."""

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
    ) -> CopyEvent:
        """Emit a copy event."""

        event = CopyEvent(str(name), str(session_id), dict(payload or {}))
        for callback in tuple(self._listeners.get(event.name, ())):
            callback(event)
        for callback in tuple(self._listeners.get("*", ())):
            callback(event)
        return event

    def clear(self) -> None:
        """Remove all copy event listeners."""

        self._listeners.clear()

from __future__ import annotations

from typing import Protocol

from engine.geometry.events import GeometryEvent, GeometryEvents


class GeometryObserver(Protocol):
    """Protocol implemented by geometry framework observers."""

    def handle_geometry_event(self, event: GeometryEvent) -> None:
        """Handle one geometry framework event."""


class GeometryObserverRegistry:
    """Registers observers against the geometry event bus."""

    def __init__(self, events: GeometryEvents) -> None:
        """Create an observer registry bound to an event bus."""

        self._events = events
        self._observers: list[GeometryObserver] = []

    def register(self, observer: GeometryObserver) -> None:
        """Register an observer for all geometry events."""

        if observer in self._observers:
            return
        self._observers.append(observer)
        self._events.subscribe("*", observer.handle_geometry_event)

    def unregister(self, observer: GeometryObserver) -> None:
        """Remove a previously registered observer."""

        if observer not in self._observers:
            return
        self._observers.remove(observer)
        self._events.unsubscribe("*", observer.handle_geometry_event)

    def observers(self) -> tuple[GeometryObserver, ...]:
        """Return registered observers."""

        return tuple(self._observers)

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from engine.geometry.context import GeometryContext


class GeometryFactory:
    """Factory registry for creating geometry through approved builders."""

    def __init__(self) -> None:
        """Create an empty geometry factory."""

        self._builders: dict[str, Callable[..., Any]] = {}

    def register_builder(
        self,
        geometry_type: str,
        builder: Callable[..., Any],
    ) -> None:
        """Register a builder for a geometry type."""

        if not geometry_type.strip():
            raise ValueError("Geometry type must not be empty.")
        self._builders[geometry_type] = builder

    def unregister_builder(self, geometry_type: str) -> None:
        """Remove a registered geometry builder."""

        self._builders.pop(geometry_type, None)

    def create(
        self,
        geometry_type: str,
        context: GeometryContext,
        **parameters: Any,
    ) -> Any:
        """Create geometry by delegating to a registered builder."""

        builder = self._builders.get(geometry_type)
        if builder is None:
            raise KeyError(f"No geometry builder registered for {geometry_type!r}.")
        return builder(context=context, **parameters)

    def builders(self) -> tuple[str, ...]:
        """Return registered geometry builder identifiers."""

        return tuple(self._builders)

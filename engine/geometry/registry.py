from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class GeometryRegistryRecord:
    """Metadata record for a registered geometry object."""

    geometry_id: str
    geometry_type: str
    geometry: Any
    owner_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class GeometryRegistry:
    """Registry of geometry framework objects and ownership metadata."""

    def __init__(self) -> None:
        """Create an empty geometry registry."""

        self._records: dict[str, GeometryRegistryRecord] = {}

    def register(
        self,
        geometry: Any,
        *,
        geometry_id: str | None = None,
        geometry_type: str | None = None,
        owner_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> GeometryRegistryRecord:
        """Register a geometry object without taking scene ownership."""

        resolved_id = geometry_id or getattr(geometry, "id", None) or str(uuid4())
        resolved_type = geometry_type or type(geometry).__name__
        record = GeometryRegistryRecord(
            geometry_id=str(resolved_id),
            geometry_type=str(resolved_type),
            geometry=geometry,
            owner_id=str(owner_id or ""),
            metadata=dict(metadata or {}),
        )
        self._records[record.geometry_id] = record
        return record

    def unregister(self, geometry_id: str) -> GeometryRegistryRecord | None:
        """Remove a geometry object from the registry."""

        return self._records.pop(str(geometry_id), None)

    def get(self, geometry_id: str) -> GeometryRegistryRecord | None:
        """Return a geometry record by id."""

        return self._records.get(str(geometry_id))

    def contains(self, geometry_id: str) -> bool:
        """Return True when a geometry id is registered."""

        return str(geometry_id) in self._records

    def records(self) -> tuple[GeometryRegistryRecord, ...]:
        """Return all registered geometry records."""

        return tuple(self._records.values())

    def by_owner(self, owner_id: str) -> tuple[GeometryRegistryRecord, ...]:
        """Return all geometry records for an owner id."""

        return tuple(
            record for record in self._records.values()
            if record.owner_id == owner_id
        )

    def clear(self) -> None:
        """Clear all geometry registry records."""

        self._records.clear()

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.geometry import Vector3
from engine.snapping.snapping_filter import SnappingFilter
from engine.snapping.snapping_plane import SnappingPlane
from engine.snapping.snapping_settings import SnappingSettings


@dataclass
class SnappingContext:
    """Runtime context for resolving snap candidates."""

    workspace: Any
    point: Vector3
    camera: Any = None
    selection_manager: Any = None
    geometry_kernel: Any = None
    transform_manager: Any = None
    plane: SnappingPlane = field(default_factory=SnappingPlane)
    settings: SnappingSettings = field(default_factory=SnappingSettings)
    filters: SnappingFilter = field(default_factory=SnappingFilter)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_workspace(
        cls,
        workspace: Any,
        point: Vector3,
        *,
        camera: Any = None,
        settings: SnappingSettings | None = None,
        filters: SnappingFilter | None = None,
    ) -> "SnappingContext":
        """Create a snapping context from existing workspace services."""

        return cls(
            workspace=workspace,
            point=point,
            camera=camera,
            selection_manager=getattr(workspace, "selection", None),
            geometry_kernel=getattr(workspace, "geometry_kernel", None),
            transform_manager=getattr(workspace, "transform_manager", None),
            settings=settings or SnappingSettings(),
            filters=filters or SnappingFilter(),
        )

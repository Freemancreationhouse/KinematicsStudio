from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from engine.geometry import Vector3


class SnappingTargetType(str, Enum):
    """Supported professional CAD snap target identifiers."""

    ENDPOINT = "Endpoint"
    MIDPOINT = "Midpoint"
    CENTER = "Center"
    INTERSECTION = "Intersection"
    NEAREST = "Nearest"
    QUADRANT = "Quadrant"
    TANGENT = "Tangent"
    PERPENDICULAR = "Perpendicular"
    PARALLEL = "Parallel"
    GRID = "Grid"
    ORIGIN = "Origin"
    CONSTRUCTION_POINT = "Construction Point"
    CONSTRUCTION_LINE = "Construction Line"
    CONSTRUCTION_PLANE = "Construction Plane"
    REFERENCE_AXIS = "Reference Axis"
    REFERENCE_PLANE = "Reference Plane"
    REFERENCE_EDGE = "Reference Edge"
    REFERENCE_VERTEX = "Reference Vertex"
    REFERENCE_FACE = "Reference Face"
    BODY_CENTER = "Body Center"
    BOUNDING_BOX_CENTER = "Bounding Box Center"
    SELECTION_CENTER = "Selection Center"


class SnappingTargetCategory(str, Enum):
    """Filter categories used by the snapping engine."""

    GEOMETRY = "Geometry"
    CONSTRUCTION = "Construction"
    REFERENCE = "Reference"
    GRID = "Grid"
    BODIES = "Bodies"
    FACES = "Faces"
    EDGES = "Edges"
    VERTICES = "Vertices"
    SKETCHES = "Sketches"
    DIMENSIONS = "Dimensions"
    ANNOTATIONS = "Annotations"


@dataclass(frozen=True)
class SnappingTarget:
    """Immutable snap target candidate resolved from workspace state."""

    point: Vector3
    target_type: SnappingTargetType
    source: Any = None
    category: SnappingTargetCategory = SnappingTargetCategory.GEOMETRY
    label: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def mode(self) -> str:
        """Return the user-facing target mode."""

        return self.target_type.value

    @property
    def entity(self) -> Any:
        """Compatibility alias for source entity."""

        return self.source

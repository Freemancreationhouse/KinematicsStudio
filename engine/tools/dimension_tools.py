from engine.commands import AddEntityCommand
from engine.entities import (
    AlignedDimensionEntity,
    AngularDimensionEntity,
    DiameterDimensionEntity,
    LinearDimensionEntity,
    RadiusDimensionEntity,
)
from engine.geometry import Vector2
from engine.tools.tool import Tool


class _PointSequenceDimensionTool(Tool):
    """Shared point collection behavior for dimension creation tools."""

    entity_class = None
    point_count = 0
    status_text = "Tool: Dimension"

    def __init__(self):

        super().__init__()
        self.points = []
        self.preview = None

    # --------------------------------

    def deactivate(self):

        self.points = []
        self.preview = None

    # --------------------------------

    def mouse_press(self, workspace, point):

        self.points.append(Vector2(point.x, point.y))

        if len(self.points) >= self.point_count:
            entity = self._make_entity(self.points)
            workspace.command_manager.execute(AddEntityCommand(workspace.entities, entity))
            self.deactivate()

    # --------------------------------

    def mouse_move(self, workspace, point):

        if not self.points:
            return

        points = self.points + [Vector2(point.x, point.y)]
        self.preview = self._preview_entity(points)

    # --------------------------------

    def mouse_release(self, workspace, point):

        pass

    # --------------------------------

    def key_press(self, workspace, key):

        if key in ("Escape", "Esc", 0x01000000):
            self.deactivate()

    # --------------------------------

    def draw_preview(self, painter):

        if self.preview:
            self.preview.draw(painter)

    # --------------------------------

    def _preview_entity(self, points):

        if len(points) < self.point_count:
            return None

        return self._make_entity(points[:self.point_count])

    # --------------------------------

    def _make_entity(self, points):

        return self.entity_class(*[point.copy() for point in points])


class LinearDimensionTool(_PointSequenceDimensionTool):
    """Create horizontal or vertical linear dimensions."""

    entity_class = LinearDimensionEntity
    point_count = 3
    status_text = "Tool: Linear Dimension"


class AlignedDimensionTool(_PointSequenceDimensionTool):
    """Create dimensions aligned to a measured segment."""

    entity_class = AlignedDimensionEntity
    point_count = 3
    status_text = "Tool: Aligned Dimension"


class RadiusDimensionTool(_PointSequenceDimensionTool):
    """Create radial dimensions from center and radius points."""

    entity_class = RadiusDimensionEntity
    point_count = 2
    status_text = "Tool: Radius Dimension"


class DiameterDimensionTool(_PointSequenceDimensionTool):
    """Create diameter dimensions from center and radius points."""

    entity_class = DiameterDimensionEntity
    point_count = 2
    status_text = "Tool: Diameter Dimension"


class AngularDimensionTool(_PointSequenceDimensionTool):
    """Create angular dimensions from vertex and two ray points."""

    entity_class = AngularDimensionEntity
    point_count = 3
    status_text = "Tool: Angular Dimension"

    # --------------------------------

    def _make_entity(self, points):

        vertex, point1, point2 = [point.copy() for point in points[:3]]
        arc_point = Vector2(
            (point1.x + point2.x) * 0.5,
            (point1.y + point2.y) * 0.5,
        )

        return AngularDimensionEntity(vertex, point1, point2, arc_point)

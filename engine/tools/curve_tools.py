from engine.commands import AddEntityCommand
from engine.entities import PolylineEntity, SplineEntity
from engine.geometry import Vector2
from engine.tools.tool import Tool


class _CurveCreationTool(Tool):
    """Shared point-collection behavior for curve creation tools."""

    entity_class = None
    minimum_points = 2
    closed_on_finish = False
    status_text = "Tool: Curve"

    def __init__(self):

        super().__init__()
        self.points = []
        self.preview = None

    # --------------------------------

    def activate(self):

        self.deactivate()

    # --------------------------------

    def deactivate(self):

        self.points = []
        self.preview = None

    # --------------------------------

    def mouse_press(self, workspace, point):

        self.points.append(Vector2(point.x, point.y))
        self._update_preview()

    # --------------------------------

    def mouse_move(self, workspace, point):

        if not self.points:
            return

        live_points = self.points + [Vector2(point.x, point.y)]
        self.preview = self._make_entity(live_points)

    # --------------------------------

    def mouse_release(self, workspace, point):

        pass

    # --------------------------------

    def key_press(self, workspace, key):

        if key in ("Escape", "Esc", 0x01000000):
            self.deactivate()
        elif key in ("Return", "Enter", 0x01000004, 0x01000005):
            self._finish(workspace)
        elif key in ("Backspace", 0x01000003):
            self._remove_last()

    # --------------------------------

    def draw_preview(self, painter):

        if self.preview:
            self.preview.draw(painter)

    # --------------------------------

    def _finish(self, workspace):

        if len(self.points) < self.minimum_points:
            self.deactivate()
            return

        entity = self._make_entity(self.points)
        workspace.command_manager.execute(AddEntityCommand(workspace.entities, entity))
        self.deactivate()

    # --------------------------------

    def _remove_last(self):

        if self.points:
            self.points.pop()
            self._update_preview()

    # --------------------------------

    def _update_preview(self):

        self.preview = self._make_entity(self.points) if len(self.points) >= 2 else None

    # --------------------------------

    def _make_entity(self, points):

        return self.entity_class([point.copy() for point in points])


class PolylineTool(_CurveCreationTool):
    """Create open polylines with live preview and Enter confirmation."""

    entity_class = PolylineEntity
    minimum_points = 2
    status_text = "Tool: Polyline"


class ClosedPolylineTool(PolylineTool):
    """Create closed polylines with live preview and Enter confirmation."""

    status_text = "Tool: Closed Polyline"

    def _make_entity(self, points):

        return PolylineEntity([point.copy() for point in points], closed=True)


class SplineTool(_CurveCreationTool):
    """Create interpolated splines with live preview and Enter confirmation."""

    entity_class = SplineEntity
    minimum_points = 2
    status_text = "Tool: Spline"

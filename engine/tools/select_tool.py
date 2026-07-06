from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPen

from engine.geometry import Vector2

from .tool import Tool


class SelectTool(Tool):

    def __init__(self):

        super().__init__()

        self.start = None
        self.current = None
        self.dragging = False

    # --------------------------------

    def deactivate(self):

        self.start = None
        self.current = None
        self.dragging = False

    # --------------------------------

    def mouse_press(self, workspace, point, additive=False):

        if workspace is None:
            return

        self.start = Vector2(point.x, point.y)
        self.current = self.start.copy()
        self.dragging = False
        self.additive = additive

    # --------------------------------

    def mouse_move(self, workspace, point):

        if self.start is None:
            return

        self.current = Vector2(point.x, point.y)

        if self.start.distance_to(self.current) > 3.0:
            self.dragging = True

    # --------------------------------

    def mouse_release(self, workspace, point, additive=False):

        if workspace is None or self.start is None:
            self.deactivate()
            return

        self.current = Vector2(point.x, point.y)

        if self.dragging:
            self._select_window(workspace, self.additive or additive)
        else:
            self._select_at_point(workspace, self.current, self.additive or additive)

        self.deactivate()

    # --------------------------------

    def draw_preview(self, painter):

        if not self.dragging or self.start is None or self.current is None:
            return

        left = min(self.start.x, self.current.x)
        top = min(self.start.y, self.current.y)
        width = abs(self.current.x - self.start.x)
        height = abs(self.current.y - self.start.y)

        painter.save()
        pen = QPen(QColor("#4fc3f7"), 1, Qt.DashLine)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QColor(79, 195, 247, 30))
        painter.drawRect(QRectF(left, top, width, height))
        painter.restore()

    # --------------------------------

    def _select_at_point(self, workspace, point, additive):

        selection = self._selection(workspace)

        candidates = (
            workspace.selectable_entities()
            if hasattr(workspace, "selectable_entities")
            else workspace.entities
        )

        for entity in reversed(candidates):
            if getattr(entity, "visible", True) and entity.hit_test(point):
                if additive:
                    selection.toggle(entity)
                else:
                    selection.select(entity)
                return

        selection.clear()

    # --------------------------------

    def _select_window(self, workspace, additive):

        selection = self._selection(workspace)

        if not additive:
            selection.clear()

        left_to_right = self.current.x >= self.start.x

        left = min(self.start.x, self.current.x)
        right = max(self.start.x, self.current.x)
        top = min(self.start.y, self.current.y)
        bottom = max(self.start.y, self.current.y)

        candidates = (
            workspace.selectable_entities()
            if hasattr(workspace, "selectable_entities")
            else workspace.entities
        )

        for entity in candidates:
            box = entity.bounding_box

            if left_to_right:
                matched = (
                    box.min.x >= left and
                    box.max.x <= right and
                    box.min.y >= top and
                    box.max.y <= bottom
                )
            else:
                matched = (
                    box.max.x >= left and
                    box.min.x <= right and
                    box.max.y >= top and
                    box.min.y <= bottom
                )

            if matched:
                selection.select(entity, True)

    # --------------------------------

    def _selection(self, workspace):

        if hasattr(workspace, "selection"):
            return workspace.selection

        from engine.workspace.selection_manager import SelectionManager

        workspace.selection = SelectionManager()
        return workspace.selection

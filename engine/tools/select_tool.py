from PySide6.QtCore import QLineF, QRectF, Qt
from PySide6.QtGui import QColor, QPen

from engine.geometry import Vector2

from .tool import Tool


class SelectTool(Tool):

    def __init__(self):

        super().__init__()

        self.start = None
        self.current = None
        self.dragging = False
        self.mode = "window"
        self.path = []

    # --------------------------------

    def deactivate(self):

        self.start = None
        self.current = None
        self.dragging = False
        self.path = []

    # --------------------------------

    def mouse_press(self, workspace, point, additive=False):

        if workspace is None:
            return

        self.start = Vector2(point.x, point.y)
        self.current = self.start.copy()
        self.dragging = False
        self.additive = additive
        self.path = [self.start.copy()]

    # --------------------------------

    def mouse_move(self, workspace, point):

        if self.start is None:
            return

        self.current = Vector2(point.x, point.y)
        self.path.append(self.current.copy())

        if self.start.distance_to(self.current) > 3.0:
            self.dragging = True

    # --------------------------------

    def mouse_release(self, workspace, point, additive=False):

        if workspace is None or self.start is None:
            self.deactivate()
            return

        self.current = Vector2(point.x, point.y)

        if self.dragging:
            self._select_drag(workspace, self.additive or additive)
        else:
            self._select_at_point(workspace, self.current, self.additive or additive)

        self.deactivate()

    # --------------------------------

    def draw_preview(self, painter):

        if not self.dragging or self.start is None or self.current is None:
            return

        painter.save()
        pen = QPen(QColor("#4fc3f7"), 1, Qt.DashLine)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QColor(79, 195, 247, 30))

        if self.mode in ("fence", "lasso") and len(self.path) > 1:
            for start, end in zip(self.path, self.path[1:]):
                painter.drawLine(QLineF(start.x, start.y, end.x, end.y))
        else:
            left = min(self.start.x, self.current.x)
            top = min(self.start.y, self.current.y)
            width = abs(self.current.x - self.start.x)
            height = abs(self.current.y - self.start.y)
            painter.drawRect(QRectF(left, top, width, height))

        painter.restore()

    # --------------------------------

    def _select_at_point(self, workspace, point, additive):

        selection = self._selection(workspace)
        entity = selection.cycle_at_point(workspace, point, additive)

        if entity is None and not additive:
            selection.clear()

    # --------------------------------

    def _select_drag(self, workspace, additive):

        selection = self._selection(workspace)

        if self.mode == "fence":
            selection.select_fence(workspace, self.path, additive)
            return

        if self.mode == "lasso":
            selection.select_lasso(workspace, self.path, True, additive)
            return

        crossing = self.current.x < self.start.x
        selection.select_window(workspace, self.start, self.current, crossing, additive)

    # --------------------------------

    def _selection(self, workspace):

        if hasattr(workspace, "selection"):
            return workspace.selection

        from engine.workspace.selection_manager import SelectionManager

        workspace.selection = SelectionManager()
        return workspace.selection

    # --------------------------------

    def _select_entities(self, selection, entities, additive):

        first = True

        for entity in entities:
            if additive:
                selection.toggle(entity)
            else:
                selection.select(entity, not first)
                first = False

    # --------------------------------

    def key_press(self, workspace, key):

        if key in ("Escape", "Esc", 0x01000000):
            self.deactivate()
        elif key in ("F", "f"):
            self.mode = "fence"
        elif key in ("L", "l"):
            self.mode = "lasso"
        elif key in ("W", "w"):
            self.mode = "window"
        elif key in ("P", "p") and workspace is not None:
            self._selection(workspace).recall_previous(workspace)
        elif key in ("I", "i") and workspace is not None:
            self._selection(workspace).invert(workspace)
        elif key in ("S", "s") and workspace is not None:
            self._selection(workspace).select_similar(workspace)

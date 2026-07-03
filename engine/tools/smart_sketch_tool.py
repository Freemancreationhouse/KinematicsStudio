from engine.tools.tool import Tool
from engine.geometry import Vector2

# Uses your existing Smart Sketch engine
from engine.smart_sketch.smart_sketch_engine import SmartSketchEngine


class SmartSketchTool(Tool):

    def __init__(self):

        super().__init__()

        self.engine = SmartSketchEngine()

        self.drawing = False

    # --------------------------------

    def mouse_press(self, workspace, point):

        self.engine.reset()

        self.engine.add_point(

            Vector2(point.x, point.y)

        )

        self.drawing = True

    # --------------------------------

    def mouse_move(self, workspace, point):

        if not self.drawing:

            return

        self.engine.add_point(

            Vector2(point.x, point.y)

        )

    # --------------------------------

    def mouse_release(self, workspace, point):

        if not self.drawing:

            return

        self.engine.add_point(

            Vector2(point.x, point.y)

        )

        entity = self.engine.finish()

        if entity is not None:

            workspace.add_entity(entity)

        self.drawing = False

    # --------------------------------

    def draw_preview(self, painter):

        pass
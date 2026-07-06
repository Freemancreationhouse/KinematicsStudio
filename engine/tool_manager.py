# DEPRECATED: Legacy tool manager retained for backward compatibility.
# V2 uses engine.tools.tool_manager.ToolManager.

from copy import deepcopy

from PySide6.QtCore import Qt

from engine.tools.line_tool import LineTool
from engine.tools.rectangle_tool import RectangleTool
from engine.tools.circle_tool import CircleTool
from engine.tools.select_tool import SelectTool
from engine.tools.move_tool import MoveTool
from engine.tools.trim_tool import TrimTool
from engine.tools.offset_tool import OffsetTool
from engine.tools.mirror_tool import MirrorTool
from engine.tools.smart_sketch_tool import SmartSketchTool

from engine.commands.add_command import AddCommand
from engine.commands.delete_command import DeleteCommand

from engine.snap.snap_manager import SnapManager


class ToolManager:

    def __init__(self):

        self.snap_manager = SnapManager()

        # -----------------------------
        # Smart Sketch (independent)
        # -----------------------------

        self.smart_tool = SmartSketchTool()
        self.smart_sketch_enabled = False

        # -----------------------------
        # Normal CAD Tools
        # -----------------------------

        self.tools = {

            "select": SelectTool(),
            "move": MoveTool(),

            "polyline": LineTool(),
            "rectangle": RectangleTool(),
            "circle": CircleTool(),

            "trim": TrimTool(),
            "offset": OffsetTool(),
            "mirror": MirrorTool(),

        }

        self.tools["polyline"].snap_manager = self.snap_manager
        self.tools["rectangle"].snap_manager = self.snap_manager
        self.tools["circle"].snap_manager = self.snap_manager

        self.current_tool = self.tools["polyline"]

    # ======================================================

    def toggle_smart_sketch(self):

        self.smart_sketch_enabled = not self.smart_sketch_enabled

        print(
            "Smart Sketch :",
            self.smart_sketch_enabled
        )

    # ======================================================

    def set_tool(self, name):

        if name in self.tools:

            self.current_tool = self.tools[name]

            print("Current Tool :", name)

    # ======================================================

    def toggle_snap(self, mode):

        if mode == "endpoint":

            self.snap_manager.endpoint = not self.snap_manager.endpoint

            print(
                "Endpoint :",
                self.snap_manager.endpoint
            )

        elif mode == "midpoint":

            self.snap_manager.midpoint = not self.snap_manager.midpoint

            print(
                "Midpoint :",
                self.snap_manager.midpoint
            )

        elif mode == "center":

            self.snap_manager.center = not self.snap_manager.center

            print(
                "Center :",
                self.snap_manager.center
            )

        elif mode == "intersection":

            self.snap_manager.intersection = (
                not self.snap_manager.intersection
            )

            print(
                "Intersection :",
                self.snap_manager.intersection
            )

    # ======================================================

    def mouse_press(self, canvas, event):

        if self.smart_sketch_enabled:

            self.smart_tool.mouse_press(canvas, event)

        else:

            self.current_tool.mouse_press(canvas, event)

    # ======================================================

    def mouse_move(self, canvas, event):

        if self.smart_sketch_enabled:

            self.smart_tool.mouse_move(canvas, event)

        else:

            self.current_tool.mouse_move(canvas, event)

    # ======================================================

    def mouse_release(self, canvas, event):

        if self.smart_sketch_enabled:

            self.smart_tool.mouse_release(canvas, event)

        elif hasattr(self.current_tool, "mouse_release"):

            self.current_tool.mouse_release(canvas, event)

    # ======================================================

    def key_press(self, canvas, event):

        ctrl = event.modifiers() & Qt.ControlModifier

        if event.key() == Qt.Key_Delete:

            if canvas.project.selected is not None:

                canvas.project.command_manager.do(

                    DeleteCommand(

                        canvas.project,

                        canvas.project.selected

                    )

                )

                canvas.project.selected = None

                canvas.update()

                return

        elif ctrl and event.key() == Qt.Key_C:

            if canvas.project.selected is not None:

                canvas.project.clipboard.copy(

                    deepcopy(canvas.project.selected)

                )

                print("Copied")

                return

        elif ctrl and event.key() == Qt.Key_V:

            entity = canvas.project.clipboard.paste()

            if entity is None:

                return

            entity = deepcopy(entity)

            if hasattr(entity, "start"):

                entity.start += entity.start.__class__(20, 20)
                entity.end += entity.end.__class__(20, 20)

            elif hasattr(entity, "p1"):

                entity.p1 += entity.p1.__class__(20, 20)
                entity.p2 += entity.p2.__class__(20, 20)

            elif hasattr(entity, "center"):

                entity.center += entity.center.__class__(20, 20)

            canvas.project.command_manager.do(

                AddCommand(

                    canvas.project,

                    entity

                )

            )

            canvas.update()

    # ======================================================

    def draw(self, painter):

        if self.smart_sketch_enabled:

            self.smart_tool.draw_preview(painter)

        elif hasattr(self.current_tool, "draw_preview"):

            self.current_tool.draw_preview(painter)

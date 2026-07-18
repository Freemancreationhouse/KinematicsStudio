from engine.entities import PolylineEntity, SplineEntity
from engine.geometry import Vector2
from engine.tools import ClosedPolylineTool, PolylineTool, SplineTool
from engine.workspace import Workspace


workspace = Workspace("Curve Tools")

polyline_tool = PolylineTool()
polyline_tool.mouse_press(workspace, Vector2(0, 0))
polyline_tool.mouse_move(workspace, Vector2(50, 0))
assert polyline_tool.preview is not None
polyline_tool.mouse_press(workspace, Vector2(50, 0))
polyline_tool.mouse_press(workspace, Vector2(50, 50))
polyline_tool.key_press(workspace, "Enter")
assert workspace.count == 1
assert isinstance(workspace.entities[0], PolylineEntity)
assert workspace.entities[0].count == 3

workspace.command_manager.undo()
assert workspace.count == 0
workspace.command_manager.redo()
assert workspace.count == 1

closed_tool = ClosedPolylineTool()
closed_tool.mouse_press(workspace, Vector2(0, 0))
closed_tool.mouse_press(workspace, Vector2(10, 0))
closed_tool.mouse_press(workspace, Vector2(10, 10))
closed_tool.key_press(workspace, "Enter")
assert workspace.entities[-1].closed

spline_tool = SplineTool()
spline_tool.mouse_press(workspace, Vector2(0, 0))
spline_tool.mouse_press(workspace, Vector2(50, 100))
spline_tool.mouse_move(workspace, Vector2(100, 0))
assert spline_tool.preview is not None
spline_tool.mouse_press(workspace, Vector2(100, 0))
spline_tool.key_press(workspace, "Enter")
assert isinstance(workspace.entities[-1], SplineEntity)
assert workspace.entities[-1].count == 3

spline_tool.mouse_press(workspace, Vector2(0, 0))
spline_tool.key_press(workspace, "Escape")
assert not spline_tool.points
assert spline_tool.preview is None

print("curve-tools-ok")

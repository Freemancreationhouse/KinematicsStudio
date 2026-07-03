from engine.tools import RectangleTool
from engine.workspace import Workspace
from engine.geometry import Vector2

tool = RectangleTool()

ws = Workspace()

tool.mouse_press(ws, Vector2(0, 0))
tool.mouse_move(ws, Vector2(100, 50))
tool.mouse_press(ws, Vector2(100, 50))

print(ws.count)
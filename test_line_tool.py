from engine.tools import LineTool
from engine.workspace import Workspace
from engine.geometry import Vector2

tool = LineTool()

ws = Workspace()

tool.mouse_press(ws, Vector2(0, 0))
tool.mouse_move(ws, Vector2(100, 0))
tool.mouse_press(ws, Vector2(100, 0))

print(ws.count)
from engine.tools import CircleTool
from engine.workspace import Workspace
from engine.geometry import Vector2

tool = CircleTool()

ws = Workspace()

tool.mouse_press(ws, Vector2(100, 100))
tool.mouse_move(ws, Vector2(150, 100))
tool.mouse_press(ws, Vector2(150, 100))

print(ws.count)
print(ws.entities[0].radius)
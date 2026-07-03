from engine.tools import MoveTool
from engine.workspace import Workspace
from engine.entities import RectangleEntity
from engine.geometry import Vector2

ws = Workspace()

rect = RectangleEntity(
    Vector2(0, 0),
    Vector2(100, 50)
)

ws.add_entity(rect)

tool = MoveTool()

tool.mouse_press(ws, Vector2(10, 10))
tool.mouse_move(ws, Vector2(30, 40))
tool.mouse_release(ws, Vector2(30, 40))

print(rect.p1)
print(rect.p2)
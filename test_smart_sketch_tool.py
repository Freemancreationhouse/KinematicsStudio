from engine.tools import SmartSketchTool
from engine.workspace import Workspace
from engine.geometry import Vector2

tool = SmartSketchTool()

ws = Workspace()

tool.mouse_press(ws, Vector2(0, 0))

for i in range(100):

    tool.mouse_move(

        ws,

        Vector2(i, 0)

    )

tool.mouse_release(

    ws,

    Vector2(100, 0)

)

print(ws.count)
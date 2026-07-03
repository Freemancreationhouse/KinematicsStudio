from engine.workspace import Workspace
from engine.entities import LineEntity
from engine.geometry import Vector2

ws = Workspace("CAD")

ws.add_entity(
        
    LineEntity(

        Vector2(0, 0),

        Vector2(100, 50)

    )

)

print(ws.name)

print(ws.count)

ws.clear()

print(ws.count)
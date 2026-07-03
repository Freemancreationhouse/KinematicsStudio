from engine.entities import LineEntity
from engine.geometry import Vector2

line = LineEntity(

    Vector2(0, 0),

    Vector2(100, 50)

)

print(line.bounding_box.width)
print(line.bounding_box.height)
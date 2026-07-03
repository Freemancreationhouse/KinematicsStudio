from engine.entities import ArcEntity
from engine.geometry import Vector2

arc = ArcEntity(

    Vector2(100, 100),

    50,

    0,

    180

)

print(arc.length)

print(arc.bounding_box.width)

print(arc.bounding_box.height)
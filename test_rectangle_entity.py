from engine.entities import RectangleEntity
from engine.geometry import Vector2

rect = RectangleEntity(

    Vector2(10, 20),

    Vector2(110, 70)

)

print(rect.width)
print(rect.height)

rect.move(10, 5)

print(rect.p1)
print(rect.p2)
from engine.entities import CircleEntity
from engine.geometry import Vector2

circle = CircleEntity(

    Vector2(100, 100),

    25

)

print(circle.bounding_box.width)
print(circle.bounding_box.height)

circle.move(10, 20)

print(circle.center)
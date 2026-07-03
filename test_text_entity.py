from engine.entities import TextEntity
from engine.geometry import Vector2

text = TextEntity(

    Vector2(100, 50),

    "Studio Kinematics"

)

print(text.bounding_box.width)
print(text.bounding_box.height)

text.move(10, 20)

print(text.position)
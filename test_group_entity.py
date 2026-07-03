from engine.entities import (
    GroupEntity,
    LineEntity,
    CircleEntity,
)

from engine.geometry import Vector2

group = GroupEntity()

group.add(

    LineEntity(

        Vector2(0, 0),

        Vector2(100, 0)

    )

)

group.add(

    CircleEntity(

        Vector2(50, 50),

        25

    )

)

print(group.count)

print(group.bounding_box.width)

print(group.bounding_box.height)
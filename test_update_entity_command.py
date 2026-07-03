from engine.commands import (

    CommandManager,

    UpdateEntityCommand

)

from engine.entities import CircleEntity

from engine.geometry import Vector2


circle = CircleEntity(

    Vector2(100, 100),

    25

)

new_circle = circle.clone()

new_circle.radius = 75


manager = CommandManager()

manager.execute(

    UpdateEntityCommand(

        circle,

        new_circle

    )

)

print(circle.radius)

manager.undo()

print(circle.radius)

manager.redo()

print(circle.radius)
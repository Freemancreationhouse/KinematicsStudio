from engine.commands import (

    CommandManager,

    MoveEntityCommand

)

from engine.entities import RectangleEntity

from engine.geometry import Vector2


rect = RectangleEntity(

    Vector2(0, 0),

    Vector2(100, 50)

)

manager = CommandManager()

manager.execute(

    MoveEntityCommand(

        rect,

        10,

        20

    )

)

print(rect.p1)

manager.undo()

print(rect.p1)

manager.redo()

print(rect.p1)
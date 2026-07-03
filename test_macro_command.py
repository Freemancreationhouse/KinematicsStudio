from engine.commands import (
    MacroCommand,
    MoveEntityCommand,
)

from engine.entities import RectangleEntity
from engine.geometry import Vector2


rect = RectangleEntity(

    Vector2(0, 0),

    Vector2(100, 50)

)

macro = MacroCommand("Move Rectangle")

macro.add(

    MoveEntityCommand(rect, 10, 0)

)

macro.add(

    MoveEntityCommand(rect, 0, 20)

)

macro.execute()

print(rect.p1)

macro.undo()

print(rect.p1)
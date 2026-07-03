from engine.commands import (
    CommandManager,
    AddEntityCommand,
)

from engine.entities import LineEntity
from engine.geometry import Vector2

entities = []

line = LineEntity(

    Vector2(0, 0),

    Vector2(100, 0)

)

manager = CommandManager()

manager.execute(

    AddEntityCommand(

        entities,

        line

    )

)

print(len(entities))

manager.undo()

print(len(entities))

manager.redo()

print(len(entities))
from engine.commands import (
    CommandManager,
    RemoveEntityCommand,
)

from engine.entities import LineEntity
from engine.geometry import Vector2

entities = [

    LineEntity(

        Vector2(0, 0),

        Vector2(100, 0)

    )

]

manager = CommandManager()

manager.execute(

    RemoveEntityCommand(

        entities,

        entities[0]

    )

)

print(len(entities))

manager.undo()

print(len(entities))

manager.redo()

print(len(entities))
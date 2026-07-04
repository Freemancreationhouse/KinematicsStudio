from engine.commands.command import Command


class MoveEntityCommand(Command):

    def __init__(self, entity, dx, dy):

        if isinstance(entity, (list, tuple)):
            self.entities = list(entity)
        else:
            self.entities = [entity]

        self.dx = dx
        self.dy = dy

    # --------------------------------

    def execute(self):

        for entity in self.entities:

            entity.move(

                self.dx,

                self.dy

            )

    # --------------------------------

    def undo(self):

        for entity in self.entities:

            entity.move(

                -self.dx,

                -self.dy

            )

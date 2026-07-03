from engine.commands.command import Command


class MoveEntityCommand(Command):

    def __init__(self, entity, dx, dy):

        self.entity = entity

        self.dx = dx
        self.dy = dy

    # --------------------------------

    def execute(self):

        self.entity.move(

            self.dx,

            self.dy

        )

    # --------------------------------

    def undo(self):

        self.entity.move(

            -self.dx,

            -self.dy

        )
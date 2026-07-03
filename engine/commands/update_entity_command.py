from copy import deepcopy

from engine.commands.command import Command


class UpdateEntityCommand(Command):

    def __init__(self, entity, new_entity):

        self.entity = entity

        self.before = deepcopy(entity.__dict__)

        self.after = deepcopy(new_entity.__dict__)

    # --------------------------------

    def execute(self):

        self.entity.__dict__.update(

            deepcopy(self.after)

        )

    # --------------------------------

    def undo(self):

        self.entity.__dict__.update(

            deepcopy(self.before)

        )
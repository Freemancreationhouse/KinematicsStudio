from engine.commands.command import Command


class RemoveEntityCommand(Command):

    def __init__(self, entity_list, entity):

        self.entity_list = entity_list
        self.entity = entity

    # --------------------------------

    def execute(self):

        if self.entity in self.entity_list:

            self.entity_list.remove(self.entity)

    # --------------------------------

    def undo(self):

        if self.entity not in self.entity_list:

            self.entity_list.append(self.entity)
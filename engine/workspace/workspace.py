from engine.commands import CommandManager
from engine.workspace.selection_manager import SelectionManager


class Workspace:

    def __init__(self, name="Workspace"):

        self.name = name

        self.entities = []

        self.selection = SelectionManager()

        self.command_manager = CommandManager()

    # --------------------------------

    def add_entity(self, entity):

        self.entities.append(entity)

    # --------------------------------

    def remove_entity(self, entity):

        if entity in self.entities:

            self.entities.remove(entity)

    # --------------------------------

    def clear(self):

        self.entities.clear()

    # --------------------------------

    @property
    def count(self):

        return len(self.entities)

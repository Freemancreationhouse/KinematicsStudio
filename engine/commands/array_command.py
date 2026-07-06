from engine.commands.command import Command


class ArrayEntityCommand(Command):
    """Add rectangular array entities as one undoable command."""

    def __init__(self, workspace, array_entities):

        self.workspace = workspace
        self.array_entities = list(array_entities)

    # --------------------------------

    def execute(self):

        for entity in self.array_entities:
            if entity not in self.workspace.entities:
                self.workspace.entities.append(entity)

    # --------------------------------

    def undo(self):

        for entity in list(self.array_entities):
            if entity in self.workspace.entities:
                self.workspace.entities.remove(entity)


class ArrayCommand(ArrayEntityCommand):
    """Backward-compatible alias for the V2 rectangular array command."""

    pass

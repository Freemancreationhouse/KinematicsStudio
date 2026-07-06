from engine.commands.command import Command


class CopyEntityCommand(Command):
    """Add copied entities to the workspace as one undoable command."""

    def __init__(self, workspace, copied_entities):

        self.workspace = workspace
        self.copied_entities = list(copied_entities)

    # --------------------------------

    def execute(self):

        for entity in self.copied_entities:
            if entity not in self.workspace.entities:
                self.workspace.entities.append(entity)

    # --------------------------------

    def undo(self):

        for entity in list(self.copied_entities):
            if entity in self.workspace.entities:
                self.workspace.entities.remove(entity)


class CopyCommand(CopyEntityCommand):
    """Backward-compatible alias for the V2 copy command."""

    pass

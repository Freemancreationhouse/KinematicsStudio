from engine.commands.command import Command


class OffsetEntityCommand(Command):
    """Add offset entities generated from a source entity."""

    def __init__(self, workspace, source, offset_entities):

        self.workspace = workspace
        self.source = source
        self.offset_entities = list(offset_entities)

    # --------------------------------

    def execute(self):

        for entity in self.offset_entities:
            if entity not in self.workspace.entities:
                self.workspace.entities.append(entity)

    # --------------------------------

    def undo(self):

        for entity in list(self.offset_entities):
            if entity in self.workspace.entities:
                self.workspace.entities.remove(entity)


class OffsetCommand(OffsetEntityCommand):
    """Backward-compatible alias for the V2 offset command."""

    pass

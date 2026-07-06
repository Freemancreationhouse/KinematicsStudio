from engine.commands.command import Command


class ExtendEntityCommand(Command):
    """Replace an extended entity with one or more resulting entities."""

    def __init__(self, workspace, target, replacements):

        self.workspace = workspace
        self.target = target
        self.replacements = list(replacements)
        self.index = None

    # --------------------------------

    def execute(self):

        entities = self.workspace.entities

        if self.target in entities:
            self.index = entities.index(self.target)
            entities.pop(self.index)

        insert_at = self.index if self.index is not None else len(entities)

        for offset, entity in enumerate(self.replacements):
            if entity not in entities:
                entities.insert(insert_at + offset, entity)

    # --------------------------------

    def undo(self):

        entities = self.workspace.entities

        for entity in list(self.replacements):
            if entity in entities:
                entities.remove(entity)

        insert_at = self.index if self.index is not None else len(entities)

        if self.target not in entities:
            entities.insert(insert_at, self.target)


class ExtendCommand(ExtendEntityCommand):
    """Backward-compatible alias for the V2 extend command."""

    pass

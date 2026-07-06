from engine.commands.command import Command


class ChamferEntityCommand(Command):
    """Replace two line entities with chamfer result geometry."""

    def __init__(self, workspace, targets, replacements):

        self.workspace = workspace
        self.targets = list(targets)
        self.replacements = list(replacements)
        self.index = None

    # --------------------------------

    def execute(self):

        entities = self.workspace.entities
        indexes = [
            entities.index(target)
            for target in self.targets
            if target in entities
        ]
        self.index = min(indexes) if indexes else self.index

        for target in list(self.targets):
            if target in entities:
                entities.remove(target)

        insert_at = self.index if self.index is not None else len(entities)
        source = self.targets[0] if self.targets else None

        if source is not None:
            self.workspace.assign_replacement_layer(source, self.replacements)

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

        for offset, target in enumerate(self.targets):
            if target not in entities:
                entities.insert(insert_at + offset, target)


class ChamferCommand(ChamferEntityCommand):
    """Backward-compatible alias for the V2 chamfer command."""

    pass

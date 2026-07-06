from engine.commands.command import Command


class ScaleEntityCommand(Command):
    """Replace entities with scaled geometry and restore originals on undo."""

    def __init__(self, workspace, replacements):

        self.workspace = workspace
        self.replacements = [
            (source, list(result))
            for source, result in replacements
        ]
        self.indexes = {}

    # --------------------------------

    def execute(self):

        entities = self.workspace.entities

        for source, result in self.replacements:
            if source in entities:
                index = entities.index(source)
                self.indexes[source] = index
                entities.pop(index)

                for offset, entity in enumerate(result):
                    entities.insert(index + offset, entity)

    # --------------------------------

    def undo(self):

        entities = self.workspace.entities

        for source, result in reversed(self.replacements):
            for entity in list(result):
                if entity in entities:
                    entities.remove(entity)

            index = self.indexes.get(source, len(entities))

            if source not in entities:
                entities.insert(index, source)


class ScaleCommand(ScaleEntityCommand):
    """Backward-compatible alias for the V2 scale command."""

    pass

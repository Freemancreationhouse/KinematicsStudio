from engine.commands.command import Command


class MirrorEntityCommand(Command):
    """Replace entities with mirrored geometry and restore originals on undo."""

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
                self.workspace.assign_replacement_layer(source, result)

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


class MirrorCommand(MirrorEntityCommand):
    """Backward-compatible alias for the V2 mirror command."""

    pass

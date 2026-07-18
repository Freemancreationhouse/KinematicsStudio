from engine.commands.command import Command
from engine.entities import BlockReference


class CreateBlockCommand(Command):
    """Create a block definition and optionally replace source entities."""

    def __init__(
        self,
        workspace,
        name,
        origin,
        entities,
        replace=True,
    ):

        self.workspace = workspace
        self.block_name = workspace.block_manager.unique_name(name)
        self.origin = origin.copy()
        self.entities = list(entities)
        self.replace = replace
        self.definition = None
        self.reference = None

    # --------------------------------

    def execute(self):

        if self.definition is None:
            clones = [self._clone_entity(entity) for entity in self.entities]
            self.definition = self.workspace.block_manager.create_definition(
                self.block_name,
                self.origin,
                clones,
            )
            self.reference = BlockReference(
                self.definition,
                self.origin.copy(),
            )

        if self.definition not in self.workspace.block_manager.definitions:
            self._restore_definition()

        if self.replace:
            for entity in list(self.entities):
                if entity in self.workspace.entities:
                    self.workspace.entities.remove(entity)

            if self.reference not in self.workspace.entities:
                self.workspace.entities.append(self.reference)

            selection = getattr(self.workspace, "selection", None)

            if selection:
                selection.clear()
                selection.select(self.reference)

    # --------------------------------

    def undo(self):

        if self.replace and self.reference in self.workspace.entities:
            self.workspace.entities.remove(self.reference)

        if self.replace:
            for entity in self.entities:
                if entity not in self.workspace.entities:
                    self.workspace.entities.append(entity)

        manager = self.workspace.block_manager

        if self.definition in manager.definitions:
            manager.remove(self.definition)

        selection = getattr(self.workspace, "selection", None)

        if selection:
            selection.clear()

            for entity in self.entities:
                if entity in self.workspace.entities:
                    selection.select(entity, True)

    # --------------------------------

    def _restore_definition(self):

        manager = self.workspace.block_manager
        manager.definitions.append(self.definition)
        manager._by_name[self.definition.name] = self.definition
        manager._by_id[self.definition.id] = self.definition
        manager.current = self.definition

    # --------------------------------

    def _clone_entity(self, entity):

        clone = entity.clone()
        clone.selected = False
        clone.visible = getattr(entity, "visible", True)
        clone.locked = getattr(entity, "locked", False)
        clone.layer = getattr(entity, "layer", None)
        clone.layer_id = getattr(entity, "layer_id", None)
        clone.layer_name = getattr(entity, "layer_name", None)
        clone.color = getattr(entity, "color", None)

        return clone


class InsertBlockCommand(Command):
    """Insert a BlockReference into the workspace."""

    def __init__(self, workspace, definition, insertion_point):

        self.workspace = workspace
        self.reference = BlockReference(definition, insertion_point.copy())

    # --------------------------------

    def execute(self):

        if self.reference not in self.workspace.entities:
            self.workspace.entities.append(self.reference)

    # --------------------------------

    def undo(self):

        if self.reference in self.workspace.entities:
            self.workspace.entities.remove(self.reference)


class EditBlockCommand(Command):
    """Replace a block definition's entities while preserving references."""

    def __init__(self, definition, new_entities, block_manager=None):

        self.definition = definition
        self.block_manager = block_manager
        self.before = [entity.clone() for entity in definition.entities]
        self.after = [entity.clone() for entity in new_entities]

    # --------------------------------

    def execute(self):

        if (
            self.block_manager is not None and
            not self.block_manager.can_update(self.definition, self.after)
        ):
            raise ValueError("Circular block references are not allowed")

        self.definition.entities = [entity.clone() for entity in self.after]

    # --------------------------------

    def undo(self):

        self.definition.entities = [entity.clone() for entity in self.before]


class ExplodeBlockCommand(Command):
    """Replace a BlockReference with transformed contained entities."""

    def __init__(self, workspace, reference):

        self.workspace = workspace
        self.reference = reference
        self.exploded = reference.exploded_entities()

    # --------------------------------

    def execute(self):

        if self.reference in self.workspace.entities:
            self.workspace.entities.remove(self.reference)

        for entity in self.exploded:
            if entity not in self.workspace.entities:
                self.workspace.entities.append(entity)

        self._select(self.exploded)

    # --------------------------------

    def undo(self):

        for entity in list(self.exploded):
            if entity in self.workspace.entities:
                self.workspace.entities.remove(entity)

        if self.reference not in self.workspace.entities:
            self.workspace.entities.append(self.reference)

        self._select([self.reference])

    # --------------------------------

    def _select(self, entities):

        selection = getattr(self.workspace, "selection", None)

        if not selection:
            return

        selection.clear()

        for entity in entities:
            if entity in self.workspace.entities:
                selection.select(entity, True)

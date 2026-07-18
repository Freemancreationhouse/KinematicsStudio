from engine.commands.command import Command


class RemoveEntityCommand(Command):
    """Remove one entity while preserving undoable workspace relationships."""

    def __init__(self, entity_list, entity):

        self.entity_list = entity_list
        self.entity = entity
        self.index = None
        self.constraints = []

    # --------------------------------

    def execute(self):

        if self.entity in self.entity_list:
            workspace = getattr(self.entity_list, "workspace", None)
            self.index = self.entity_list.index(self.entity)

            if workspace is not None and hasattr(workspace, "constraint_manager"):
                self.constraints = workspace.constraint_manager.constraints_for_entity(
                    self.entity
                )

            self.entity_list.remove(self.entity)

    # --------------------------------

    def undo(self):

        if self.entity not in self.entity_list:
            workspace = getattr(self.entity_list, "workspace", None)
            index = self.index if self.index is not None else len(self.entity_list)

            self.entity_list.insert(min(index, len(self.entity_list)), self.entity)

            if workspace is not None and hasattr(workspace, "constraint_manager"):
                for constraint in self.constraints:
                    workspace.constraint_manager.add(constraint)

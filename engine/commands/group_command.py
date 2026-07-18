from engine.commands.command import Command


class CreateGroupCommand(Command):
    """Create a group containing existing workspace entities."""

    def __init__(self, workspace, name, entities):

        self.workspace = workspace
        self.group_name = workspace.group_manager.unique_name(name)
        self.entities = list(entities)
        self.group = None

    # --------------------------------

    def execute(self):

        if self.group is None:
            self.group = self.workspace.group_manager.create(
                self.group_name,
                self.entities
            )
            return

        self._restore_group()

    # --------------------------------

    def undo(self):

        self.workspace.group_manager.remove(self.group)

    # --------------------------------

    def _restore_group(self):

        manager = self.workspace.group_manager

        if self.group in manager.groups:
            return

        manager.groups.append(self.group)
        manager._by_name[self.group.name] = self.group
        manager._by_id[self.group.id] = self.group
        manager.current = self.group


class DeleteGroupCommand(Command):
    """Remove a group without deleting its entities."""

    def __init__(self, workspace, group):

        self.workspace = workspace
        self.group = group

    # --------------------------------

    def execute(self):

        self.workspace.group_manager.remove(self.group)

    # --------------------------------

    def undo(self):

        manager = self.workspace.group_manager

        if self.group not in manager.groups:
            manager.groups.append(self.group)
            manager._by_name[self.group.name] = self.group
            manager._by_id[self.group.id] = self.group
            manager.current = self.group


class RenameGroupCommand(Command):
    """Rename a group through the command system."""

    def __init__(self, workspace, group, new_name):

        self.workspace = workspace
        self.group = group
        self.before = group.name
        self.after = str(new_name).strip()

    # --------------------------------

    def execute(self):

        self.workspace.group_manager.rename(self.group, self.after)

    # --------------------------------

    def undo(self):

        self.workspace.group_manager.rename(self.group, self.before)


class AddEntityToGroupCommand(Command):
    """Add an existing entity reference to a group."""

    def __init__(self, workspace, group, entity):

        self.workspace = workspace
        self.group = group
        self.entity = entity

    # --------------------------------

    def execute(self):

        self.workspace.group_manager.add_entity(self.group, self.entity)

    # --------------------------------

    def undo(self):

        self.workspace.group_manager.remove_entity(self.group, self.entity)


class RemoveEntityFromGroupCommand(Command):
    """Remove an entity reference from a group."""

    def __init__(self, workspace, group, entity):

        self.workspace = workspace
        self.group = group
        self.entity = entity

    # --------------------------------

    def execute(self):

        self.workspace.group_manager.remove_entity(self.group, self.entity)

    # --------------------------------

    def undo(self):

        self.workspace.group_manager.add_entity(self.group, self.entity)


class UngroupCommand(DeleteGroupCommand):
    """Backward-compatible command name for removing group membership."""

    pass

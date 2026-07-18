from engine.commands.command import Command


class AddSectionPlaneCommand(Command):
    """Undoable command for adding a 3D section plane."""

    def __init__(self, workspace, section):

        self.workspace = workspace
        self.section = section

    # --------------------------------

    def execute(self):
        """Add the section plane and select it."""

        self.workspace.section_manager.add(self.section)
        self.workspace.assign_layer(self.section)
        self.workspace.selection.select(self.section)

    # --------------------------------

    def undo(self):
        """Remove the section plane."""

        self.workspace.section_manager.remove(self.section)
        self.workspace.selection.unregister_entity(self.section)
        self.workspace.unregister_layer_entity(self.section)


class RemoveSectionPlaneCommand(Command):
    """Undoable command for removing a 3D section plane."""

    def __init__(self, workspace, section):

        self.workspace = workspace
        self.section = section

    # --------------------------------

    def execute(self):
        """Remove the section plane."""

        self.workspace.section_manager.remove(self.section)
        self.workspace.selection.unregister_entity(self.section)
        self.workspace.unregister_layer_entity(self.section)

    # --------------------------------

    def undo(self):
        """Restore the section plane."""

        self.workspace.section_manager.add(self.section)
        self.workspace.assign_layer(self.section)


class UpdateSectionPlaneCommand(Command):
    """Undoable command for changing section plane state."""

    def __init__(self, section, before, after):

        self.section = section
        self.before = dict(before)
        self.after = dict(after)

    # --------------------------------

    def execute(self):
        """Apply the updated section state."""

        self._apply(self.after)

    # --------------------------------

    def undo(self):
        """Restore the previous section state."""

        self._apply(self.before)

    # --------------------------------

    def _apply(self, state):

        for key, value in state.items():
            setattr(self.section, key, value)


class SetActiveSectionCommand(Command):
    """Undoable command for changing the active section plane."""

    def __init__(self, workspace, before, after):

        self.workspace = workspace
        self.before = before
        self.after = after

    # --------------------------------

    def execute(self):
        """Activate the target section plane."""

        self.workspace.section_manager.set_active(self.after)

    # --------------------------------

    def undo(self):
        """Restore the previous active section plane."""

        self.workspace.section_manager.set_active(self.before)

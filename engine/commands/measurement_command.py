from engine.commands.command import Command


class AddMeasurementCommand(Command):
    """Undoable command for adding a persistent 3D measurement."""

    def __init__(self, workspace, measurement):

        self.workspace = workspace
        self.measurement = measurement

    # --------------------------------

    def execute(self):
        """Add the measurement and select it."""

        self.workspace.measurement_manager.add(self.measurement)
        self.workspace.selection.select(self.measurement)

    # --------------------------------

    def undo(self):
        """Remove the measurement."""

        self.workspace.measurement_manager.remove(self.measurement)
        self.workspace.selection.unregister_entity(self.measurement)


class RemoveMeasurementCommand(Command):
    """Undoable command for removing a persistent 3D measurement."""

    def __init__(self, workspace, measurement):

        self.workspace = workspace
        self.measurement = measurement

    # --------------------------------

    def execute(self):
        """Remove the measurement."""

        self.workspace.measurement_manager.remove(self.measurement)
        self.workspace.selection.unregister_entity(self.measurement)

    # --------------------------------

    def undo(self):
        """Restore the measurement."""

        self.workspace.measurement_manager.add(self.measurement)

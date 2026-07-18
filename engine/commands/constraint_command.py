from copy import deepcopy

from engine.commands.command import Command


class CreateConstraintCommand(Command):
    """Create a constraint through the workspace ConstraintManager."""

    def __init__(self, workspace, constraint_type, entities, value=None, name=None, driven=False):

        self.workspace = workspace
        self.constraint_type = constraint_type
        self.entities = list(entities)
        self.value = value
        self.constraint_name = name
        self.driven = driven
        self.constraint = None

    # --------------------------------

    def execute(self):

        if self.constraint is None:
            self.constraint = self.workspace.constraint_manager.create(
                self.constraint_type,
                self.entities,
                self.value,
                self.constraint_name,
                self.driven,
            )
        else:
            self.workspace.constraint_manager.add(self.constraint)

    # --------------------------------

    def undo(self):

        self.workspace.constraint_manager.remove(self.constraint)


class DeleteConstraintCommand(Command):
    """Remove a constraint through the command system."""

    def __init__(self, workspace, constraint):

        self.workspace = workspace
        self.constraint = constraint

    # --------------------------------

    def execute(self):

        self.workspace.constraint_manager.remove(self.constraint)

    # --------------------------------

    def undo(self):

        self.workspace.constraint_manager.add(self.constraint)


class RenameConstraintCommand(Command):
    """Rename a constraint through the command system."""

    def __init__(self, workspace, constraint, new_name):

        self.workspace = workspace
        self.constraint = constraint
        self.before = constraint.name
        self.after = str(new_name).strip()

    # --------------------------------

    def execute(self):

        self.workspace.constraint_manager.rename(self.constraint, self.after)

    # --------------------------------

    def undo(self):

        self.workspace.constraint_manager.rename(self.constraint, self.before)


class UpdateConstraintCommand(Command):
    """Undoable update for constraint values and state."""

    def __init__(self, workspace, constraint, before, after):

        self.workspace = workspace
        self.constraint = constraint
        self.before = deepcopy(before)
        self.after = deepcopy(after)

    # --------------------------------

    def execute(self):

        self._apply(self.after)

    # --------------------------------

    def undo(self):

        self._apply(self.before)

    # --------------------------------

    def _apply(self, state):

        for key, value in state.items():
            setattr(self.constraint, key, deepcopy(value))

        self.workspace.constraint_manager.validate()


class EnableConstraintCommand(UpdateConstraintCommand):
    """Enable or disable a constraint."""

    def __init__(self, workspace, constraint, enabled):

        before = {
            "enabled": constraint.enabled,
            "suppressed": constraint.suppressed,
        }
        after = {
            "enabled": bool(enabled),
            "suppressed": not bool(enabled),
        }

        super().__init__(workspace, constraint, before, after)

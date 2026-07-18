from copy import deepcopy

from engine.commands.command import Command
from engine.geometry.curves import clone_points


class UpdateCurveVerticesCommand(Command):
    """Undoable update for polyline vertices or spline control points."""

    def __init__(self, entity, before, after, attribute=None):

        self.entity = entity
        self.attribute = attribute or self._default_attribute(entity)
        self.before = clone_points(before)
        self.after = clone_points(after)

    # --------------------------------

    def execute(self):
        """Apply updated curve points."""

        setattr(self.entity, self.attribute, clone_points(self.after))

    # --------------------------------

    def undo(self):
        """Restore previous curve points."""

        setattr(self.entity, self.attribute, clone_points(self.before))

    # --------------------------------

    def _default_attribute(self, entity):

        if hasattr(entity, "control_points"):
            return "control_points"

        return "points"


class UpdatePolylineClosedCommand(Command):
    """Undoable open/closed polyline state update."""

    def __init__(self, entity, closed):

        self.entity = entity
        self.before = bool(getattr(entity, "closed", False))
        self.after = bool(closed)

    # --------------------------------

    def execute(self):
        """Apply the new closed state."""

        self.entity.closed = self.after

    # --------------------------------

    def undo(self):
        """Restore the previous closed state."""

        self.entity.closed = self.before

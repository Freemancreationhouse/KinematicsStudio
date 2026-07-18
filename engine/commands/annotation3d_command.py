from engine.commands.command import Command


class AddAnnotation3DCommand(Command):
    """Undoable command for adding a persistent 3D annotation."""

    def __init__(self, workspace, annotation):

        self.workspace = workspace
        self.annotation = annotation

    def execute(self):
        """Add the annotation and select it."""

        self.workspace.annotation_manager3d.add(self.annotation)
        self.workspace.assign_layer(self.annotation)
        self.workspace.selection.select(self.annotation)

    def undo(self):
        """Remove the annotation."""

        self.workspace.annotation_manager3d.remove(self.annotation)
        self.workspace.selection.unregister_entity(self.annotation)
        self.workspace.unregister_layer_entity(self.annotation)


class RemoveAnnotation3DCommand(Command):
    """Undoable command for removing a persistent 3D annotation."""

    def __init__(self, workspace, annotation):

        self.workspace = workspace
        self.annotation = annotation

    def execute(self):
        """Remove the annotation."""

        self.workspace.annotation_manager3d.remove(self.annotation)
        self.workspace.selection.unregister_entity(self.annotation)
        self.workspace.unregister_layer_entity(self.annotation)

    def undo(self):
        """Restore the annotation."""

        self.workspace.annotation_manager3d.add(self.annotation)
        self.workspace.assign_layer(self.annotation)


class UpdateAnnotation3DCommand(Command):
    """Undoable command for updating annotation properties."""

    def __init__(self, annotation, before, after):

        self.annotation = annotation
        self.before = dict(before)
        self.after = dict(after)

    def execute(self):
        """Apply annotation state."""

        self._apply(self.after)

    def undo(self):
        """Restore annotation state."""

        self._apply(self.before)

    def _apply(self, state):

        for key, value in state.items():
            setattr(self.annotation, key, value)


class AddReviewItemCommand(Command):
    """Undoable command for adding a review item."""

    def __init__(self, workspace, review_item):

        self.workspace = workspace
        self.review_item = review_item

    def execute(self):
        """Add the review item."""

        self.workspace.review_manager.add(self.review_item)

    def undo(self):
        """Remove the review item."""

        self.workspace.review_manager.remove(self.review_item)


class RemoveReviewItemCommand(Command):
    """Undoable command for removing a review item."""

    def __init__(self, workspace, review_item):

        self.workspace = workspace
        self.review_item = review_item

    def execute(self):
        """Remove the review item."""

        self.workspace.review_manager.remove(self.review_item)

    def undo(self):
        """Restore the review item."""

        self.workspace.review_manager.add(self.review_item)


class UpdateReviewItemCommand(Command):
    """Undoable command for updating review item state."""

    def __init__(self, review_item, before, after):

        self.review_item = review_item
        self.before = dict(before)
        self.after = dict(after)

    def execute(self):
        """Apply review item state."""

        self._apply(self.after)

    def undo(self):
        """Restore review item state."""

        self._apply(self.before)

    def _apply(self, state):

        for key, value in state.items():
            setattr(self.review_item, key, value)

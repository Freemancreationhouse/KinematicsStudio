from engine.commands.command import Command
from engine.scene_organization import DisplayPreset, SceneCollection, ViewFilter


class CreateSceneCollectionCommand(Command):
    """Undoable command for creating a 3D scene collection."""

    def __init__(self, workspace, name, parent=None):

        self.workspace = workspace
        self.collection_name = name
        self.parent = parent
        self.collection = None

    def execute(self):
        """Create the collection."""

        if self.collection is None:
            self.collection = self.workspace.scene_collection_manager.create(
                self.collection_name,
                self.parent,
            )
        else:
            self.workspace.scene_collection_manager.add(self.collection)

    def undo(self):
        """Remove the created collection."""

        self.workspace.scene_collection_manager.delete(self.collection)


class RenameSceneCollectionCommand(Command):
    """Undoable command for renaming a 3D scene collection."""

    def __init__(self, workspace, collection, new_name):

        self.workspace = workspace
        self.collection = collection
        self.new_name = new_name
        self.old_name = None

    def execute(self):
        """Rename the collection."""

        target = self.workspace.scene_collection_manager.get(self.collection)

        if target is None:
            return

        if self.old_name is None:
            self.old_name = target.name

        self.workspace.scene_collection_manager.rename(target, self.new_name)

    def undo(self):
        """Restore the old collection name."""

        target = self.workspace.scene_collection_manager.get(self.new_name)

        if target is not None:
            target.name = self.old_name


class DeleteSceneCollectionCommand(Command):
    """Undoable command for deleting a 3D scene collection."""

    def __init__(self, workspace, collection):

        self.workspace = workspace
        self.collection = collection
        self.snapshot = None

    def execute(self):
        """Delete the collection."""

        target = self.workspace.scene_collection_manager.get(self.collection)

        if target is None:
            return

        self.snapshot = target.to_dict()
        self.workspace.scene_collection_manager.delete(target)

    def undo(self):
        """Restore the deleted collection."""

        if self.snapshot is not None:
            self.workspace.scene_collection_manager.add(SceneCollection.from_dict(self.snapshot))


class MoveEntityToCollectionCommand(Command):
    """Undoable command for moving an entity reference between collections."""

    def __init__(self, workspace, entity, collection):

        self.workspace = workspace
        self.entity = entity
        self.collection = collection
        self.previous = None

    def execute(self):
        """Move the entity reference."""

        manager = self.workspace.scene_collection_manager

        if self.previous is None:
            self.previous = manager.entity_collection(self.entity)

        manager.move_entity(self.entity, self.collection)

    def undo(self):
        """Restore the previous collection reference."""

        manager = self.workspace.scene_collection_manager
        manager.remove_entity(self.entity)

        if self.previous is not None:
            manager.move_entity(self.entity, self.previous)


class UpdateSceneCollectionCommand(Command):
    """Undoable command for updating collection state."""

    def __init__(self, collection, before, after):

        self.collection = collection
        self.before = dict(before)
        self.after = dict(after)

    def execute(self):
        """Apply collection state."""

        self._apply(self.after)

    def undo(self):
        """Restore collection state."""

        self._apply(self.before)

    def _apply(self, state):

        for key, value in state.items():
            setattr(self.collection, key, value)


class AddViewFilterCommand(Command):
    """Undoable command for adding a view filter."""

    def __init__(self, workspace, view_filter):

        self.workspace = workspace
        self.view_filter = view_filter

    def execute(self):
        """Add the filter."""

        self.workspace.view_filter_manager.add(self.view_filter)

    def undo(self):
        """Remove the filter."""

        self.workspace.view_filter_manager.delete(self.view_filter)


class RemoveViewFilterCommand(Command):
    """Undoable command for removing a view filter."""

    def __init__(self, workspace, view_filter):

        self.workspace = workspace
        self.view_filter = view_filter
        self.snapshot = None

    def execute(self):
        """Remove the filter."""

        target = self.workspace.view_filter_manager.get(self.view_filter)

        if target is None:
            return

        self.snapshot = target.to_dict()
        self.workspace.view_filter_manager.delete(target)

    def undo(self):
        """Restore the filter."""

        if self.snapshot is not None:
            self.workspace.view_filter_manager.add(ViewFilter.from_dict(self.snapshot))


class SaveDisplayPresetCommand(Command):
    """Undoable command for saving a display preset."""

    def __init__(self, workspace, name):

        self.workspace = workspace
        self.preset_name = name
        self.preset = None

    def execute(self):
        """Save the preset."""

        if self.preset is None:
            self.preset = self.workspace.display_preset_manager.save(
                self.preset_name,
                self.workspace,
            )
        else:
            self.workspace.display_preset_manager.add(self.preset)

    def undo(self):
        """Remove the saved preset."""

        self.workspace.display_preset_manager.delete(self.preset)


class RestoreDisplayPresetCommand(Command):
    """Undoable command for restoring a display preset."""

    def __init__(self, workspace, preset):

        self.workspace = workspace
        self.preset = preset
        self.before = None

    def execute(self):
        """Restore the preset."""

        if self.before is None:
            self.before = DisplayPreset.capture("Before Restore", self.workspace)

        self.workspace.display_preset_manager.restore(self.preset, self.workspace)

    def undo(self):
        """Restore previous display state."""

        if self.before is not None:
            self.before.restore(self.workspace)


class RenameDisplayPresetCommand(Command):
    """Undoable command for renaming a display preset."""

    def __init__(self, workspace, preset, new_name):

        self.workspace = workspace
        self.preset = preset
        self.new_name = new_name
        self.old_name = None

    def execute(self):
        """Rename the preset."""

        target = self.workspace.display_preset_manager.get(self.preset)

        if target is None:
            return

        if self.old_name is None:
            self.old_name = target.name

        self.workspace.display_preset_manager.rename(target, self.new_name)

    def undo(self):
        """Restore preset name."""

        target = self.workspace.display_preset_manager.get(self.new_name)

        if target is not None:
            target.name = self.old_name


class DeleteDisplayPresetCommand(Command):
    """Undoable command for deleting a display preset."""

    def __init__(self, workspace, preset):

        self.workspace = workspace
        self.preset = preset
        self.snapshot = None

    def execute(self):
        """Delete the preset."""

        target = self.workspace.display_preset_manager.get(self.preset)

        if target is None:
            return

        self.snapshot = target.to_dict()
        self.workspace.display_preset_manager.delete(target)

    def undo(self):
        """Restore deleted preset."""

        if self.snapshot is not None:
            self.workspace.display_preset_manager.add(DisplayPreset.from_dict(self.snapshot))

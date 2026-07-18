from engine.commands.command import Command


class SaveViewStateCommand(Command):
    """Undoable command for saving a named 3D view."""

    def __init__(self, workspace, name, camera):

        self.workspace = workspace
        self.view_name = name
        self.camera = camera
        self.created_view = None
        self.before = None

    # --------------------------------

    def execute(self):
        """Save the named view from the current camera."""

        manager = self.workspace.view_state_manager
        display_mode = self.workspace.display_mode_manager.current_mode
        visual_style = getattr(self.workspace.visual_style_manager.current, "name", "Default")
        existing = manager.get(self.view_name)
        self.before = existing.to_dict() if existing is not None and self.before is None else self.before
        self.created_view = manager.save_view(self.view_name, self.camera, display_mode, visual_style)

    # --------------------------------

    def undo(self):
        """Remove a new view or restore replaced data."""

        manager = self.workspace.view_state_manager

        if self.before is None:
            manager.delete(self.created_view)
            return

        from engine.view_states import ViewState

        restored = ViewState.from_dict(self.before)
        manager.delete(self.created_view)
        manager.add(restored)
        manager.current = restored


class RestoreViewStateCommand(Command):
    """Undoable command for restoring a named 3D view."""

    def __init__(self, workspace, view, camera):

        self.workspace = workspace
        self.view = view
        self.camera = camera
        self.before_camera = None
        self.before_view = None
        self.before_mode = None
        self.before_style = None

    # --------------------------------

    def execute(self):
        """Restore the target named view."""

        manager = self.workspace.view_state_manager
        target = manager.get(self.view)

        if target is None:
            return

        if self.before_camera is None:
            self.before_camera = self.camera.to_dict()
            self.before_view = manager.current
            self.before_mode = self.workspace.display_mode_manager.current_mode
            self.before_style = getattr(self.workspace.visual_style_manager.current, "name", "Default")

        manager.restore_view(target, self.camera)
        self.workspace.display_mode_manager.set_mode(target.display_mode)
        self.workspace.visual_style_manager.set_current(target.visual_style)

    # --------------------------------

    def undo(self):
        """Restore the previous camera and display state."""

        if self.before_camera is not None:
            self.camera.from_dict(self.before_camera)

        self.workspace.view_state_manager.current = self.before_view
        self.workspace.display_mode_manager.set_mode(self.before_mode)
        self.workspace.visual_style_manager.set_current(self.before_style)


class RenameViewStateCommand(Command):
    """Undoable command for renaming a named 3D view."""

    def __init__(self, workspace, view, new_name):

        self.workspace = workspace
        self.view = view
        self.new_name = new_name
        self.old_name = None

    # --------------------------------

    def execute(self):
        """Rename the target view."""

        target = self.workspace.view_state_manager.get(self.view)

        if target is None:
            return

        if self.old_name is None:
            self.old_name = target.name

        self.workspace.view_state_manager.rename(target, self.new_name)

    # --------------------------------

    def undo(self):
        """Restore the previous name."""

        target = self.workspace.view_state_manager.get(self.new_name)

        if target is not None:
            target.name = self.old_name


class DeleteViewStateCommand(Command):
    """Undoable command for deleting a named 3D view."""

    def __init__(self, workspace, view):

        self.workspace = workspace
        self.view = view
        self.snapshot = None

    # --------------------------------

    def execute(self):
        """Delete the target view."""

        fallback = (self.snapshot or {}).get("name")
        target = self.workspace.view_state_manager.get(self.view) or self.workspace.view_state_manager.get(fallback)

        if target is None:
            return

        self.snapshot = target.to_dict()
        self.workspace.view_state_manager.delete(target)

    # --------------------------------

    def undo(self):
        """Restore the deleted view."""

        if self.snapshot is None:
            return

        from engine.view_states import ViewState

        view = ViewState.from_dict(self.snapshot)
        self.workspace.view_state_manager.add(view)
        self.workspace.view_state_manager.current = view


class SetDisplayModeCommand(Command):
    """Undoable command for changing the active 3D display mode."""

    def __init__(self, workspace, mode):

        self.workspace = workspace
        self.mode = mode
        self.before = None

    # --------------------------------

    def execute(self):
        """Apply the display mode."""

        if self.before is None:
            self.before = self.workspace.display_mode_manager.current_mode

        self.workspace.display_mode_manager.set_mode(self.mode)

    # --------------------------------

    def undo(self):
        """Restore the previous display mode."""

        self.workspace.display_mode_manager.set_mode(self.before)


class SetVisualStyleCommand(Command):
    """Undoable command for changing the active visual style."""

    def __init__(self, workspace, style):

        self.workspace = workspace
        self.style = style
        self.before = None

    # --------------------------------

    def execute(self):
        """Apply the visual style."""

        if self.before is None:
            self.before = getattr(self.workspace.visual_style_manager.current, "name", "Default")

        self.workspace.visual_style_manager.set_current(self.style)

    # --------------------------------

    def undo(self):
        """Restore the previous visual style."""

        self.workspace.visual_style_manager.set_current(self.before)

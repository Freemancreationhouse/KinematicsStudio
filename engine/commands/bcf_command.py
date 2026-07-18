from engine.commands.command import Command


class AddBCFTopicCommand(Command):
    """Undoable command for adding a BCF coordination topic."""

    def __init__(self, workspace, topic, project=None):

        self.workspace = workspace
        self.topic = topic
        self.project = project

    def execute(self):
        """Add and select the topic."""

        self.workspace.bcf_manager.add_topic(self.topic, self.project)
        self.workspace.selection.select(self.topic)

    def undo(self):
        """Remove the topic."""

        self.workspace.bcf_manager.remove_topic(self.topic)
        self.workspace.selection.unregister_entity(self.topic)


class RemoveBCFTopicCommand(Command):
    """Undoable command for removing a BCF coordination topic."""

    def __init__(self, workspace, topic):

        self.workspace = workspace
        self.topic = topic
        self.project = workspace.bcf_manager.project_for_topic(topic)

    def execute(self):
        """Remove the topic."""

        self.workspace.bcf_manager.remove_topic(self.topic)
        self.workspace.selection.unregister_entity(self.topic)

    def undo(self):
        """Restore the topic."""

        self.workspace.bcf_manager.add_topic(self.topic, self.project)


class UpdateBCFTopicCommand(Command):
    """Undoable command for updating BCF topic metadata."""

    def __init__(self, topic, before, after):

        self.topic = topic
        self.before = dict(before)
        self.after = dict(after)

    def execute(self):
        """Apply topic metadata."""

        self._apply(self.after)

    def undo(self):
        """Restore previous topic metadata."""

        self._apply(self.before)

    def _apply(self, state):

        for key, value in state.items():
            if hasattr(self.topic, key):
                setattr(self.topic, key, value)


class ImportBCFProjectCommand(Command):
    """Undoable command for importing a BCF project file."""

    def __init__(self, workspace, path):

        self.workspace = workspace
        self.path = path
        self.project = None

    def execute(self):
        """Import or restore the BCF project."""

        if self.project is None:
            self.project = self.workspace.bcf_manager.import_bcf(self.path)
        else:
            self.workspace.bcf_manager.add_project(self.project)

    def undo(self):
        """Remove the imported BCF project."""

        self.workspace.bcf_manager.remove_project(self.project)
        for topic in self.project.topics:
            self.workspace.selection.unregister_entity(topic)


class RestoreBCFViewpointCommand(Command):
    """Undoable command for restoring a BCF viewpoint to a camera."""

    def __init__(self, workspace, topic, camera, viewpoint=None):

        self.workspace = workspace
        self.topic = topic
        self.camera = camera
        self.viewpoint = viewpoint
        self.before = self._camera_state()

    def execute(self):
        """Restore the BCF viewpoint."""

        if self.viewpoint is not None:
            self.viewpoint.apply_to_camera(self.camera)
        else:
            self.workspace.bcf_manager.restore_viewpoint(self.topic, self.camera)

    def undo(self):
        """Restore the previous camera state."""

        if self.camera is None:
            return

        for key, value in self.before.items():
            setattr(self.camera, key, value)

    def _camera_state(self):

        if self.camera is None:
            return {}

        return {
            "position": getattr(self.camera, "position", None),
            "target": getattr(self.camera, "target", None),
            "up": getattr(self.camera, "up", None),
        }

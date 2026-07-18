from engine.collaboration import Issue, Session
from engine.commands.command import Command


class AddSessionCommand(Command):
    """Undoable command for adding a review session."""

    def __init__(self, workspace, session):

        self.workspace = workspace
        self.session = session

    def execute(self):
        """Add the session."""

        self.workspace.collaboration_manager.add(self.session)

    def undo(self):
        """Remove the session."""

        manager = self.workspace.collaboration_manager

        if self.session in manager.sessions:
            manager.sessions.remove(self.session)
            if manager.active is self.session:
                manager.active = manager.sessions[0] if manager.sessions else None


class UpdateSessionCommand(Command):
    """Undoable command for updating session state."""

    def __init__(self, session, before, after):

        self.session = session
        self.before = dict(before)
        self.after = dict(after)

    def execute(self):
        """Apply session state."""

        self._apply(self.after)

    def undo(self):
        """Restore session state."""

        self._apply(self.before)

    def _apply(self, state):

        for key, value in state.items():
            setattr(self.session, key, value)


class ArchiveSessionCommand(Command):
    """Undoable command for archiving a review session."""

    def __init__(self, workspace, session):

        self.workspace = workspace
        self.session = session

    def execute(self):
        """Archive the session."""

        self.workspace.collaboration_manager.archive(self.session)

    def undo(self):
        """Restore the session."""

        self.workspace.collaboration_manager.restore(self.session)


class RestoreSessionCommand(Command):
    """Undoable command for restoring an archived session."""

    def __init__(self, workspace, session):

        self.workspace = workspace
        self.session = session

    def execute(self):
        """Restore the session."""

        self.workspace.collaboration_manager.restore(self.session)

    def undo(self):
        """Archive the session."""

        self.workspace.collaboration_manager.archive(self.session)


class DuplicateSessionCommand(Command):
    """Undoable command for duplicating a review session."""

    def __init__(self, workspace, session, name=None):

        self.workspace = workspace
        self.session = session
        self.duplicate_name = name
        self.duplicate = None

    def execute(self):
        """Duplicate the session."""

        if self.duplicate is None:
            self.duplicate = self.workspace.collaboration_manager.duplicate(self.session, self.duplicate_name)
        else:
            self.workspace.collaboration_manager.add(self.duplicate)

    def undo(self):
        """Remove the duplicated session."""

        manager = self.workspace.collaboration_manager

        if self.duplicate in manager.sessions:
            manager.sessions.remove(self.duplicate)


class AddIssueCommand(Command):
    """Undoable command for adding an issue marker."""

    def __init__(self, workspace, issue):

        self.workspace = workspace
        self.issue = issue

    def execute(self):
        """Add the issue and select it."""

        self.workspace.issue_manager.add(self.issue)
        self.workspace.assign_layer(self.issue)
        self.workspace.selection.select(self.issue)

    def undo(self):
        """Remove the issue."""

        self.workspace.issue_manager.remove(self.issue)
        self.workspace.selection.unregister_entity(self.issue)
        self.workspace.unregister_layer_entity(self.issue)


class RemoveIssueCommand(Command):
    """Undoable command for removing an issue marker."""

    def __init__(self, workspace, issue):

        self.workspace = workspace
        self.issue = issue

    def execute(self):
        """Remove the issue."""

        self.workspace.issue_manager.remove(self.issue)
        self.workspace.selection.unregister_entity(self.issue)
        self.workspace.unregister_layer_entity(self.issue)

    def undo(self):
        """Restore the issue."""

        self.workspace.issue_manager.add(self.issue)
        self.workspace.assign_layer(self.issue)


class UpdateIssueCommand(Command):
    """Undoable command for updating issue state."""

    def __init__(self, issue, before, after):

        self.issue = issue
        self.before = dict(before)
        self.after = dict(after)

    def execute(self):
        """Apply issue state."""

        self._apply(self.after)

    def undo(self):
        """Restore issue state."""

        self._apply(self.before)

    def _apply(self, state):

        for key, value in state.items():
            setattr(self.issue, key, value)

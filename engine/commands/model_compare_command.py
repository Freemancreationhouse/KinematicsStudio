from engine.commands.command import Command
from engine.model_compare import (
    CompareSettings,
    CompareSession,
    CompareStatistics,
    Revision,
    RevisionMetadata,
    RevisionStatistics,
)


class CreateCompareSessionCommand(Command):
    """Undoable command for creating a saved model comparison session."""

    def __init__(self, workspace, name, settings=None):

        self.workspace = workspace
        self.session_name = name
        self.settings = settings
        self.session = None

    def execute(self):
        """Create the compare session."""

        if self.session is None:
            self.session = self.workspace.model_compare_manager.create_session(
                self.session_name,
                self.workspace,
                self.settings,
            )
        else:
            self.workspace.model_compare_manager.add_session(self.session)

    def undo(self):
        """Remove the created compare session."""

        if self.session is not None:
            self.workspace.model_compare_manager.remove_session(self.session)


class RunModelCompareCommand(Command):
    """Undoable command for re-running a model comparison session."""

    def __init__(self, workspace, session=None):

        self.workspace = workspace
        self.session = session
        self.before_results = None
        self.before_statistics = None
        self.after_results = None
        self.after_statistics = None

    def execute(self):
        """Run comparison through the workspace-owned manager."""

        manager = self.workspace.model_compare_manager
        target = manager.get_session(self.session) if self.session is not None else manager.active_session

        if target is None:
            target = manager.create_session("Current Compare", self.workspace, manager.settings)

        self.session = target

        if self.before_results is None:
            self.before_results = list(target.results)
            self.before_statistics = target.statistics

        if self.after_results is None:
            target = manager.rerun(self.workspace, target)
            self.after_results = list(target.results)
            self.after_statistics = target.statistics
        else:
            target.set_results(self.after_results)
            target.statistics = self.after_statistics
            manager.active_session_id = target.id

    def undo(self):
        """Restore previous compare results."""

        manager = self.workspace.model_compare_manager
        target = manager.get_session(self.session)

        if target is None:
            return

        target.results = list(self.before_results or [])
        target.statistics = self.before_statistics or CompareStatistics()
        manager.active_session_id = target.id


class UpdateCompareSettingsCommand(Command):
    """Undoable command for updating compare settings."""

    def __init__(self, workspace, before, after):

        self.workspace = workspace
        self.before = before
        self.after = after

    def execute(self):
        """Apply compare settings."""

        self.workspace.model_compare_manager.settings = self._settings(self.after)

    def undo(self):
        """Restore compare settings."""

        self.workspace.model_compare_manager.settings = self._settings(self.before)

    def _settings(self, value):

        if isinstance(value, CompareSettings):
            return value

        return CompareSettings.from_dict(value)


class RemoveCompareSessionCommand(Command):
    """Undoable command for removing a compare session."""

    def __init__(self, workspace, session):

        self.workspace = workspace
        self.session = session
        self.removed = None

    def execute(self):
        """Remove the compare session."""

        manager = self.workspace.model_compare_manager
        self.removed = manager.get_session(self.session)

        if self.removed is not None:
            manager.remove_session(self.removed)

    def undo(self):
        """Restore the removed compare session."""

        if isinstance(self.removed, CompareSession):
            self.workspace.model_compare_manager.add_session(self.removed)


class CaptureRevisionCommand(Command):
    """Undoable command for capturing a coordination revision."""

    def __init__(self, workspace, name, metadata=None):

        self.workspace = workspace
        self.revision_name = name
        self.metadata = metadata
        self.revision = None

    def execute(self):
        """Capture or restore a revision."""

        manager = self.workspace.revision_manager

        if self.revision is None:
            metadata = (
                self.metadata
                if isinstance(self.metadata, RevisionMetadata)
                else RevisionMetadata.from_dict(self.metadata or {})
            )
            self.revision = manager.capture_revision(self.revision_name, self.workspace, metadata)
        else:
            manager.add_revision(self.revision)
            manager.timeline_manager.add_revision_event(self.revision)

    def undo(self):
        """Remove the captured revision."""

        if self.revision is not None:
            self.workspace.revision_manager.remove_revision(self.revision)
            self.workspace.selection.unregister_entity(self.revision)


class CompareRevisionsCommand(Command):
    """Undoable command for comparing two captured revisions."""

    def __init__(self, workspace, before_revision, after_revision, settings=None):

        self.workspace = workspace
        self.before_revision = before_revision
        self.after_revision = after_revision
        self.settings = settings
        self.session = None
        self.before_session_count = 0
        self.before_revision_statistics = None
        self.before_compare_session_id = None

    def execute(self):
        """Compare two revisions through ModelCompareManager."""

        manager = self.workspace.revision_manager
        after = manager.get_revision(self.after_revision)

        if after is not None and self.before_revision_statistics is None:
            self.before_revision_statistics = after.statistics
            self.before_compare_session_id = after.compare_session_id

        self.before_session_count = len(self.workspace.model_compare_manager.sessions)

        if self.session is None:
            self.session = manager.compare_revisions(self.before_revision, self.after_revision, self.settings)
        else:
            self.workspace.model_compare_manager.add_session(self.session)
            after = manager.get_revision(self.after_revision)
            if after is not None:
                after.compare_session_id = self.session.id
                after.statistics = RevisionStatistics.from_compare_statistics(self.session.statistics)
            manager.timeline_manager.add_compare_event(self.session)

    def undo(self):
        """Remove the generated compare session and restore revision state."""

        compare_manager = self.workspace.model_compare_manager
        revision_manager = self.workspace.revision_manager

        if self.session is not None:
            compare_manager.remove_session(self.session)

        after = revision_manager.get_revision(self.after_revision)

        if after is not None:
            after.statistics = self.before_revision_statistics or RevisionStatistics()
            after.compare_session_id = self.before_compare_session_id


class AddTimelineBookmarkCommand(Command):
    """Undoable command for adding a timeline bookmark."""

    def __init__(self, workspace, title, target_id, note=""):

        self.workspace = workspace
        self.title = title
        self.target_id = target_id
        self.note = note
        self.bookmark = None

    def execute(self):
        """Add the bookmark."""

        if self.bookmark is None:
            self.bookmark = self.workspace.timeline_manager.add_bookmark(
                self.title,
                self.target_id,
                self.note,
            )
        else:
            self.workspace.timeline_manager.timeline.bookmarks.append(self.bookmark)

    def undo(self):
        """Remove the bookmark."""

        bookmarks = self.workspace.timeline_manager.timeline.bookmarks

        if self.bookmark in bookmarks:
            bookmarks.remove(self.bookmark)


class UpdateRevisionFiltersCommand(Command):
    """Undoable command for revision and timeline filter settings."""

    def __init__(self, workspace, before, after):

        self.workspace = workspace
        self.before = dict(before or {})
        self.after = dict(after or {})

    def execute(self):
        """Apply revision filters."""

        self.workspace.revision_manager.filters = dict(self.after)
        self.workspace.timeline_manager.timeline.filters = dict(self.after)

    def undo(self):
        """Restore revision filters."""

        self.workspace.revision_manager.filters = dict(self.before)
        self.workspace.timeline_manager.timeline.filters = dict(self.before)

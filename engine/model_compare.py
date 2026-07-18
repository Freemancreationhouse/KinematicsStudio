from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from engine.geometry import BoundingBox3D, Vector3


CHANGE_TYPES = (
    "Added",
    "Removed",
    "Modified",
    "Moved",
    "Renamed",
    "Layer Changed",
    "Metadata Changed",
    "Reference Changed",
    "Geometry Placeholder",
)


@dataclass
class CompareSettings:
    """Reusable model comparison settings."""

    include_current: bool = True
    include_references: bool = True
    include_geometry_placeholders: bool = True
    include_metadata: bool = True
    include_layers: bool = True
    include_moved: bool = True
    search: str = ""
    group_by: str = "Change Type"

    def to_dict(self):
        """Return JSON-safe settings."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create settings from persisted data."""

        data = data or {}

        return CompareSettings(
            bool(data.get("include_current", True)),
            bool(data.get("include_references", True)),
            bool(data.get("include_geometry_placeholders", True)),
            bool(data.get("include_metadata", True)),
            bool(data.get("include_layers", True)),
            bool(data.get("include_moved", True)),
            data.get("search", ""),
            data.get("group_by", "Change Type"),
        )


@dataclass
class CompareStatistics:
    """Summary statistics for one compare session."""

    total: int = 0
    added: int = 0
    removed: int = 0
    modified: int = 0
    moved: int = 0
    renamed: int = 0
    layer_changes: int = 0
    metadata_changes: int = 0
    reference_changes: int = 0
    geometry_placeholders: int = 0

    @staticmethod
    def from_results(results):
        """Build statistics from compare results."""

        return CompareStatistics(
            len(results),
            _count(results, "Added"),
            _count(results, "Removed"),
            _count(results, "Modified"),
            _count(results, "Moved"),
            _count(results, "Renamed"),
            _count(results, "Layer Changed"),
            _count(results, "Metadata Changed"),
            _count(results, "Reference Changed"),
            _count(results, "Geometry Placeholder"),
        )

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create statistics from persisted data."""

        data = data or {}

        return CompareStatistics(
            int(data.get("total", 0)),
            int(data.get("added", 0)),
            int(data.get("removed", 0)),
            int(data.get("modified", 0)),
            int(data.get("moved", 0)),
            int(data.get("renamed", 0)),
            int(data.get("layer_changes", 0)),
            int(data.get("metadata_changes", 0)),
            int(data.get("reference_changes", 0)),
            int(data.get("geometry_placeholders", 0)),
        )


class CompareResult:
    """Persistent selectable model comparison marker."""

    type_name = "CompareResult"
    is_3d = True
    is_compare = True

    COLORS = {
        "Added": "#66bb6a",
        "Removed": "#ef5350",
        "Modified": "#ffca28",
        "Moved": "#42a5f5",
        "Renamed": "#ab47bc",
        "Layer Changed": "#26c6da",
        "Metadata Changed": "#ffa726",
        "Reference Changed": "#ec407a",
        "Geometry Placeholder": "#bdbdbd",
    }

    def __init__(
        self,
        change_type="Modified",
        object_id="",
        name="Compare Result",
        before=None,
        after=None,
        description="",
        location=None,
    ):

        self.id = str(uuid4())
        self.name = name
        self.change_type = change_type if change_type in CHANGE_TYPES else "Modified"
        self.object_id = object_id
        self.before = dict(before or {})
        self.after = dict(after or {})
        self.description = description
        self.location = location or _snapshot_location(self.after or self.before)
        self.visible = True
        self.locked = False
        self.selected = False
        self.hovered = False
        self.layer_name = None
        self.created_at = _timestamp()

    @property
    def display_color(self):
        """Return result display color."""

        return self.COLORS.get(self.change_type, "#ffffff")

    @property
    def bounding_box3d(self):
        """Return a compact marker bounds box."""

        box = BoundingBox3D()
        pad = 7.0
        box.add(self.location - Vector3(pad, pad, pad))
        box.add(self.location + Vector3(pad, pad, pad))

        return box

    def points(self):
        """Return representative marker points."""

        return [self.location]

    def segments(self):
        """Return marker cross segments."""

        pad = 7.0

        return [
            (self.location - Vector3(pad, 0.0, 0.0), self.location + Vector3(pad, 0.0, 0.0)),
            (self.location - Vector3(0.0, pad, 0.0), self.location + Vector3(0.0, pad, 0.0)),
            (self.location - Vector3(0.0, 0.0, pad), self.location + Vector3(0.0, 0.0, pad)),
        ]

    def to_dict(self):
        """Return JSON-safe result data."""

        return {
            "id": self.id,
            "name": self.name,
            "change_type": self.change_type,
            "object_id": self.object_id,
            "before": dict(self.before),
            "after": dict(self.after),
            "description": self.description,
            "location": _vector_to_data(self.location),
            "visible": self.visible,
            "locked": self.locked,
            "selected": self.selected,
            "layer_name": self.layer_name,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data):
        """Create a compare result from persisted data."""

        data = data or {}
        result = CompareResult(
            data.get("change_type", "Modified"),
            data.get("object_id", ""),
            data.get("name", "Compare Result"),
            data.get("before", {}),
            data.get("after", {}),
            data.get("description", ""),
            _vector_from_data(data.get("location")),
        )
        result.id = data.get("id", result.id)
        result.visible = bool(data.get("visible", True))
        result.locked = bool(data.get("locked", False))
        result.selected = bool(data.get("selected", False))
        result.layer_name = data.get("layer_name")
        result.created_at = data.get("created_at", result.created_at)

        return result


class CompareSession:
    """Saved model comparison session."""

    def __init__(self, name="Compare Session", settings=None, baseline=None):

        self.id = str(uuid4())
        self.name = name
        self.settings = settings or CompareSettings()
        self.baseline = list(baseline or [])
        self.results = []
        self.statistics = CompareStatistics()
        self.filters = {}
        self.view_options = {
            "show_added": True,
            "show_removed": True,
            "show_modified": True,
        }
        self.created_at = _timestamp()
        self.updated_at = self.created_at

    def set_results(self, results):
        """Store compare results and refresh statistics."""

        self.results = list(results)
        self.statistics = CompareStatistics.from_results(self.results)
        self.updated_at = _timestamp()

    def to_dict(self):
        """Return JSON-safe session data."""

        return {
            "id": self.id,
            "name": self.name,
            "settings": self.settings.to_dict(),
            "baseline": list(self.baseline),
            "results": [result.to_dict() for result in self.results],
            "statistics": self.statistics.to_dict(),
            "filters": dict(self.filters),
            "view_options": dict(self.view_options),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data):
        """Create a session from persisted data."""

        data = data or {}
        session = CompareSession(
            data.get("name", "Compare Session"),
            CompareSettings.from_dict(data.get("settings", {})),
            data.get("baseline", []),
        )
        session.id = data.get("id", session.id)
        session.results = [CompareResult.from_dict(item) for item in data.get("results", [])]
        session.statistics = CompareStatistics.from_dict(data.get("statistics", {}))
        session.filters = dict(data.get("filters", {}))
        session.view_options = dict(data.get("view_options", session.view_options))
        session.created_at = data.get("created_at", session.created_at)
        session.updated_at = data.get("updated_at", session.updated_at)

        return session


@dataclass
class RevisionMetadata:
    """Describes one coordination revision."""

    author: str = ""
    source: str = "Workspace"
    description: str = ""
    tags: tuple = ()
    reference_ids: tuple = ()

    def to_dict(self):
        """Return JSON-safe revision metadata."""

        return {
            "author": self.author,
            "source": self.source,
            "description": self.description,
            "tags": list(self.tags),
            "reference_ids": list(self.reference_ids),
        }

    @staticmethod
    def from_dict(data):
        """Create metadata from persisted data."""

        data = data or {}

        return RevisionMetadata(
            data.get("author", ""),
            data.get("source", "Workspace"),
            data.get("description", ""),
            tuple(data.get("tags", [])),
            tuple(data.get("reference_ids", [])),
        )


@dataclass
class RevisionStatistics:
    """Summary statistics for a captured revision."""

    object_count: int = 0
    reference_count: int = 0
    change_count: int = 0
    added: int = 0
    removed: int = 0
    modified: int = 0
    moved: int = 0
    metadata_changes: int = 0
    reference_changes: int = 0

    @staticmethod
    def from_snapshot(snapshot):
        """Create revision statistics from snapshot data."""

        snapshot = list(snapshot or [])

        return RevisionStatistics(
            len(snapshot),
            len([item for item in snapshot if item.get("source") == "Reference"]),
        )

    @staticmethod
    def from_compare_statistics(statistics):
        """Create revision statistics from compare statistics."""

        statistics = statistics or CompareStatistics()

        return RevisionStatistics(
            0,
            0,
            statistics.total,
            statistics.added,
            statistics.removed,
            statistics.modified,
            statistics.moved,
            statistics.metadata_changes,
            statistics.reference_changes,
        )

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create statistics from persisted data."""

        data = data or {}

        return RevisionStatistics(
            int(data.get("object_count", 0)),
            int(data.get("reference_count", 0)),
            int(data.get("change_count", 0)),
            int(data.get("added", 0)),
            int(data.get("removed", 0)),
            int(data.get("modified", 0)),
            int(data.get("moved", 0)),
            int(data.get("metadata_changes", 0)),
            int(data.get("reference_changes", 0)),
        )


class Revision:
    """Persistent selectable coordination revision marker."""

    type_name = "Revision"
    is_3d = True
    is_revision = True

    def __init__(self, name="Revision", metadata=None, snapshot=None, location=None):

        self.id = str(uuid4())
        self.name = name
        self.metadata = metadata or RevisionMetadata()
        self.snapshot = list(snapshot or [])
        self.statistics = RevisionStatistics.from_snapshot(self.snapshot)
        self.compare_session_id = None
        self.viewpoint = {}
        self.bookmarks = []
        self.filters = {}
        self.visible = True
        self.locked = False
        self.selected = False
        self.hovered = False
        self.layer_name = None
        self.created_at = _timestamp()
        self.location = location or _snapshot_collection_location(self.snapshot)

    @property
    def display_color(self):
        """Return revision marker color."""

        return "#7e57c2"

    @property
    def bounding_box3d(self):
        """Return compact marker bounds for rendering and picking."""

        box = BoundingBox3D()
        pad = 9.0
        box.add(self.location - Vector3(pad, pad, pad))
        box.add(self.location + Vector3(pad, pad, pad))

        return box

    def points(self):
        """Return representative marker points."""

        return [self.location]

    def segments(self):
        """Return revision diamond marker segments."""

        pad = 9.0
        left = self.location - Vector3(pad, 0.0, 0.0)
        right = self.location + Vector3(pad, 0.0, 0.0)
        top = self.location + Vector3(0.0, pad, 0.0)
        bottom = self.location - Vector3(0.0, pad, 0.0)

        return [(left, top), (top, right), (right, bottom), (bottom, left)]

    def to_dict(self):
        """Return JSON-safe revision data."""

        return {
            "id": self.id,
            "name": self.name,
            "metadata": self.metadata.to_dict(),
            "snapshot": list(self.snapshot),
            "statistics": self.statistics.to_dict(),
            "compare_session_id": self.compare_session_id,
            "viewpoint": dict(self.viewpoint),
            "bookmarks": list(self.bookmarks),
            "filters": dict(self.filters),
            "visible": self.visible,
            "locked": self.locked,
            "selected": self.selected,
            "layer_name": self.layer_name,
            "created_at": self.created_at,
            "location": _vector_to_data(self.location),
        }

    @staticmethod
    def from_dict(data):
        """Create a revision from persisted data."""

        data = data or {}
        revision = Revision(
            data.get("name", "Revision"),
            RevisionMetadata.from_dict(data.get("metadata", {})),
            data.get("snapshot", []),
            _vector_from_data(data.get("location")),
        )
        revision.id = data.get("id", revision.id)
        revision.statistics = RevisionStatistics.from_dict(data.get("statistics", {}))
        revision.compare_session_id = data.get("compare_session_id")
        revision.viewpoint = dict(data.get("viewpoint", {}))
        revision.bookmarks = list(data.get("bookmarks", []))
        revision.filters = dict(data.get("filters", {}))
        revision.visible = bool(data.get("visible", True))
        revision.locked = bool(data.get("locked", False))
        revision.selected = bool(data.get("selected", False))
        revision.layer_name = data.get("layer_name")
        revision.created_at = data.get("created_at", revision.created_at)

        return revision


class RevisionTimeline:
    """Stores revision, compare and session timeline entries."""

    def __init__(self):

        self.entries = []
        self.bookmarks = []
        self.filters = {}

    def add_entry(self, entry_type, title, target_id="", payload=None):
        """Add a timeline entry."""

        entry = {
            "id": str(uuid4()),
            "type": entry_type,
            "title": title,
            "target_id": target_id,
            "payload": dict(payload or {}),
            "created_at": _timestamp(),
        }
        self.entries.append(entry)

        return entry

    def add_bookmark(self, title, target_id, note=""):
        """Add a timeline bookmark."""

        bookmark = {
            "id": str(uuid4()),
            "title": title,
            "target_id": target_id,
            "note": note,
            "created_at": _timestamp(),
        }
        self.bookmarks.append(bookmark)

        return bookmark

    def filtered_entries(self, search=""):
        """Return timeline entries filtered by title and type."""

        query = (search or "").lower().strip()

        if not query:
            return list(self.entries)

        return [
            entry for entry in self.entries
            if query in entry.get("title", "").lower() or query in entry.get("type", "").lower()
        ]

    def to_dict(self):
        """Return JSON-safe timeline data."""

        return {
            "entries": list(self.entries),
            "bookmarks": list(self.bookmarks),
            "filters": dict(self.filters),
        }

    def from_dict(self, data):
        """Restore timeline data."""

        data = data or {}
        self.entries = list(data.get("entries", []))
        self.bookmarks = list(data.get("bookmarks", []))
        self.filters = dict(data.get("filters", {}))


class TimelineManager:
    """Coordinates revision, session and comparison timeline state."""

    def __init__(self, revision_manager=None):

        self.revision_manager = revision_manager
        self.timeline = RevisionTimeline()
        self.active_revision_id = None
        self.current_entry_id = None
        self.review_settings = {}

    def add_revision_event(self, revision):
        """Record a revision capture in the timeline."""

        entry = self.timeline.add_entry(
            "Revision",
            revision.name,
            revision.id,
            {"statistics": revision.statistics.to_dict()},
        )
        self.current_entry_id = entry["id"]

        return entry

    def add_compare_event(self, session):
        """Record a compare run in the timeline."""

        entry = self.timeline.add_entry(
            "Compare",
            session.name,
            session.id,
            {"statistics": session.statistics.to_dict()},
        )
        self.current_entry_id = entry["id"]

        return entry

    def add_session_event(self, session):
        """Record a compare session in the timeline."""

        entry = self.timeline.add_entry("Session", session.name, session.id)
        self.current_entry_id = entry["id"]

        return entry

    def add_bookmark(self, title, target_id, note=""):
        """Store a timeline bookmark."""

        return self.timeline.add_bookmark(title, target_id, note)

    def jump_to_revision(self, revision):
        """Make a revision the active timeline target."""

        target = self.revision_manager.get_revision(revision) if self.revision_manager is not None else None

        if target is None:
            return None

        self.active_revision_id = target.id
        self.current_entry_id = target.id

        return target

    def restore_viewpoint(self, revision):
        """Return a persisted revision viewpoint for callers that own the camera."""

        target = self.revision_manager.get_revision(revision) if self.revision_manager is not None else None

        return dict(getattr(target, "viewpoint", {}) or {}) if target is not None else {}

    def filtered_entries(self, search=""):
        """Return filtered timeline entries."""

        return self.timeline.filtered_entries(search)

    def to_dict(self):
        """Return JSON-safe timeline manager data."""

        return {
            "timeline": self.timeline.to_dict(),
            "active_revision_id": self.active_revision_id,
            "current_entry_id": self.current_entry_id,
            "review_settings": dict(self.review_settings),
        }

    def from_dict(self, data):
        """Restore timeline manager data."""

        data = data or {}
        self.timeline.from_dict(data.get("timeline", {}))
        self.active_revision_id = data.get("active_revision_id")
        self.current_entry_id = data.get("current_entry_id")
        self.review_settings = dict(data.get("review_settings", {}))


class RevisionManager:
    """Owns revision history on top of the existing compare framework."""

    def __init__(self, compare_manager=None):

        self.compare_manager = compare_manager
        self.revisions = []
        self.active_revision_id = None
        self.filters = {}
        self.visible = True
        self.timeline_manager = TimelineManager(self)

    @property
    def active_revision(self):
        """Return the active revision."""

        if not self.revisions:
            return None

        return self.get_revision(self.active_revision_id) or self.revisions[-1]

    def capture_revision(self, name, workspace, metadata=None):
        """Capture workspace state as a revision."""

        snapshot = self.compare_manager.snapshot_workspace(workspace) if self.compare_manager is not None else []
        revision = Revision(name, metadata or RevisionMetadata(), snapshot)
        self.add_revision(revision)
        self.timeline_manager.add_revision_event(revision)

        return revision

    def add_revision(self, revision):
        """Store a revision."""

        if revision not in self.revisions:
            self.revisions.append(revision)

        self.active_revision_id = revision.id
        self.timeline_manager.active_revision_id = revision.id

        return revision

    def remove_revision(self, revision):
        """Remove a revision."""

        target = self.get_revision(revision)

        if target is None:
            return False

        self.revisions.remove(target)
        if self.active_revision_id == target.id:
            self.active_revision_id = self.revisions[-1].id if self.revisions else None
            self.timeline_manager.active_revision_id = self.active_revision_id

        return True

    def compare_revisions(self, before_revision, after_revision, settings=None):
        """Compare two revisions using ModelCompareManager."""

        before = self.get_revision(before_revision)
        after = self.get_revision(after_revision)

        if before is None or after is None or self.compare_manager is None:
            return None

        settings = settings or self.compare_manager.settings
        session = CompareSession(f"Revision Compare: {before.name} → {after.name}", settings, before.snapshot)
        session.set_results(self.compare_manager.compare_snapshots(before.snapshot, after.snapshot, settings))
        self.compare_manager.add_session(session)
        after.compare_session_id = session.id
        after.statistics = RevisionStatistics.from_compare_statistics(session.statistics)
        self.active_revision_id = after.id
        self.timeline_manager.active_revision_id = after.id
        self.timeline_manager.add_compare_event(session)

        return session

    def jump_to_revision(self, revision):
        """Activate a revision for navigation/review."""

        target = self.timeline_manager.jump_to_revision(revision)

        if target is not None:
            self.active_revision_id = target.id

        return target

    def restore_viewpoint(self, revision):
        """Return stored viewpoint data for UI/camera callers."""

        return self.timeline_manager.restore_viewpoint(revision)

    def search(self, query=""):
        """Search revisions by name, description, source or tags."""

        query = (query or "").lower().strip()

        if not query:
            return list(self.revisions)

        return [
            revision for revision in self.revisions
            if (
                query in revision.name.lower() or
                query in revision.metadata.description.lower() or
                query in revision.metadata.source.lower() or
                any(query in tag.lower() for tag in revision.metadata.tags)
            )
        ]

    def grouped_revisions(self, group_by="Source"):
        """Return revisions grouped for UI consumers."""

        groups = {}

        for revision in self.search(self.filters.get("search", "")):
            group = revision.metadata.source if group_by == "Source" else revision.created_at[:10]
            groups.setdefault(group, []).append(revision)

        return groups

    def summary(self):
        """Return revision history summary data."""

        active = self.active_revision

        return {
            "revisions": len(self.revisions),
            "timeline_entries": len(self.timeline_manager.timeline.entries),
            "bookmarks": len(self.timeline_manager.timeline.bookmarks),
            "active_revision": active.name if active is not None else "",
        }

    def visible_revisions(self):
        """Return visible revision markers."""

        if not self.visible:
            return []

        return [revision for revision in self.revisions if revision.visible]

    def get_revision(self, revision):
        """Return a revision by object, id or name."""

        if isinstance(revision, Revision):
            return revision if revision in self.revisions else None

        for item in self.revisions:
            if item.id == revision or item.name == revision:
                return item

        return None

    def to_dict(self):
        """Return JSON-safe revision manager data."""

        return {
            "visible": self.visible,
            "active_revision_id": self.active_revision_id,
            "filters": dict(self.filters),
            "revisions": [revision.to_dict() for revision in self.revisions],
            "timeline_manager": self.timeline_manager.to_dict(),
        }

    def from_dict(self, data):
        """Restore revision manager data."""

        data = data or {}
        self.visible = bool(data.get("visible", True))
        self.active_revision_id = data.get("active_revision_id")
        self.filters = dict(data.get("filters", {}))
        self.revisions = [Revision.from_dict(item) for item in data.get("revisions", [])]
        self.timeline_manager.from_dict(data.get("timeline_manager", {}))
        self.timeline_manager.revision_manager = self


class ModelCompareManager:
    """Workspace-owned model comparison and change tracking manager."""

    def __init__(self):

        self.sessions = []
        self.active_session_id = None
        self.settings = CompareSettings()
        self.visible = True
        self.revision_manager = RevisionManager(self)
        self.timeline_manager = self.revision_manager.timeline_manager

    @property
    def active_session(self):
        """Return the active compare session."""

        if not self.sessions:
            return None

        return self.get_session(self.active_session_id) or self.sessions[-1]

    def create_session(self, name, workspace, settings=None):
        """Create a saved compare session from current workspace state."""

        session = CompareSession(name, settings or self.settings, self.snapshot_workspace(workspace, settings))
        self.add_session(session)

        return session

    def add_session(self, session):
        """Store a compare session."""

        if session not in self.sessions:
            self.sessions.append(session)

        self.active_session_id = session.id
        self.timeline_manager.add_session_event(session)

        return session

    def remove_session(self, session):
        """Remove a compare session."""

        target = self.get_session(session)

        if target is None:
            return False

        self.sessions.remove(target)
        if self.active_session_id == target.id:
            self.active_session_id = self.sessions[-1].id if self.sessions else None

        return True

    def rerun(self, workspace, session=None):
        """Re-run comparison against the session baseline."""

        target = self.get_session(session) if session is not None else self.active_session

        if target is None:
            target = self.create_session("Current Compare", workspace, self.settings)

        current = self.snapshot_workspace(workspace, target.settings)
        results = self.compare_snapshots(target.baseline, current, target.settings)
        target.set_results(results)
        self.active_session_id = target.id

        return target

    def compare_current_vs_reference(self, workspace, reference_model=None, settings=None):
        """Compare current Scene3D objects against one reference model snapshot."""

        settings = settings or self.settings
        current = _current_snapshots(workspace) if settings.include_current else []
        reference = _reference_snapshots(workspace, reference_model)
        session = CompareSession("Current vs Reference", settings, reference)
        session.set_results(self.compare_snapshots(reference, current, settings))
        self.add_session(session)

        return session

    def compare_reference_vs_reference(self, workspace, reference_a, reference_b, settings=None):
        """Compare two reference model snapshots."""

        settings = settings or self.settings
        before = _reference_snapshots(workspace, reference_a)
        after = _reference_snapshots(workspace, reference_b)
        session = CompareSession("Reference vs Reference", settings, before)
        session.set_results(self.compare_snapshots(before, after, settings))
        self.add_session(session)

        return session

    def snapshot_workspace(self, workspace, settings=None):
        """Create a comparison snapshot from workspace state."""

        settings = settings or self.settings
        snapshots = []

        if settings.include_current:
            snapshots.extend(_current_snapshots(workspace))

        if settings.include_references:
            snapshots.extend(_reference_snapshots(workspace))

        return snapshots

    def compare_snapshots(self, before, after, settings=None):
        """Compare two snapshot collections."""

        settings = settings or self.settings
        before_map = {item["id"]: item for item in before}
        after_map = {item["id"]: item for item in after}
        results = []

        for object_id, item in after_map.items():
            if object_id not in before_map:
                results.append(_result("Added", object_id, None, item))

        for object_id, item in before_map.items():
            if object_id not in after_map:
                results.append(_result("Removed", object_id, item, None))

        for object_id in sorted(set(before_map).intersection(after_map)):
            results.extend(_changed_results(object_id, before_map[object_id], after_map[object_id], settings))

        return self.filtered_results(results, settings)

    def filtered_results(self, results=None, settings=None):
        """Return compare results filtered by search text."""

        settings = settings or self.settings
        query = settings.search.lower().strip()
        source = list(results if results is not None else self.results())

        if not query:
            return source

        return [
            result for result in source
            if query in result.name.lower() or query in result.change_type.lower() or query in result.description.lower()
        ]

    def grouped_results(self, group_by=None):
        """Return visible results grouped for UI consumers."""

        key = group_by or self.settings.group_by
        groups = {}

        for result in self.visible_results():
            group = result.change_type if key == "Change Type" else getattr(result, "name", "Compare")
            groups.setdefault(group, []).append(result)

        return groups

    def visible_results(self):
        """Return visible compare results from the active session."""

        if not self.visible:
            return []

        return [result for result in self.results() if result.visible]

    def results(self):
        """Return active session results."""

        session = self.active_session

        return list(session.results) if session is not None else []

    def get_session(self, session):
        """Return a session by object, id or name."""

        if isinstance(session, CompareSession):
            return session if session in self.sessions else None

        for item in self.sessions:
            if item.id == session or item.name == session:
                return item

        return None

    def get_result(self, result):
        """Return a compare result by object, id or name."""

        if isinstance(result, CompareResult):
            return result if result in self.results() else None

        for item in self.results():
            if item.id == result or item.name == result:
                return item

        return None

    def to_dict(self):
        """Return JSON-safe manager data."""

        return {
            "visible": self.visible,
            "active_session_id": self.active_session_id,
            "settings": self.settings.to_dict(),
            "sessions": [session.to_dict() for session in self.sessions],
            "revision_manager": self.revision_manager.to_dict(),
        }

    def from_dict(self, data):
        """Restore persisted manager data."""

        data = data or {}
        self.visible = bool(data.get("visible", True))
        self.active_session_id = data.get("active_session_id")
        self.settings = CompareSettings.from_dict(data.get("settings", {}))
        self.sessions = [CompareSession.from_dict(item) for item in data.get("sessions", [])]
        self.revision_manager.from_dict(data.get("revision_manager", {}))
        self.revision_manager.compare_manager = self
        self.timeline_manager = self.revision_manager.timeline_manager


def _changed_results(object_id, before, after, settings):

    results = []

    if before.get("name") != after.get("name"):
        results.append(_result("Renamed", object_id, before, after, "Name changed."))

    if settings.include_layers and before.get("layer") != after.get("layer"):
        results.append(_result("Layer Changed", object_id, before, after, "Layer assignment changed."))

    if settings.include_moved and before.get("location") != after.get("location"):
        results.append(_result("Moved", object_id, before, after, "Object location changed."))

    if settings.include_metadata and before.get("metadata") != after.get("metadata"):
        results.append(_result("Metadata Changed", object_id, before, after, "Metadata changed."))

    if before.get("reference") != after.get("reference"):
        results.append(_result("Reference Changed", object_id, before, after, "Reference linkage changed."))

    if before.get("signature") != after.get("signature"):
        results.append(_result("Modified", object_id, before, after, "Object signature changed."))

    if settings.include_geometry_placeholders and before.get("geometry") != after.get("geometry"):
        results.append(_result("Geometry Placeholder", object_id, before, after, "Geometry comparison placeholder."))

    return results


def _current_snapshots(workspace):

    scene = getattr(workspace, "scene3d", None)

    if scene is None:
        return []

    return [_entity_snapshot(entity, "Current") for entity in scene.entities()]


def _reference_snapshots(workspace, reference_model=None):

    manager = getattr(workspace, "reference_manager", None)

    if manager is None:
        return []

    target = manager.get_model(reference_model) if reference_model is not None and hasattr(manager, "get_model") else reference_model
    models = [target] if target is not None else list(manager.models)

    return [_reference_snapshot(model) for model in models if model is not None]


def _entity_snapshot(entity, source):

    box = getattr(entity, "bounding_box3d", BoundingBox3D())

    return {
        "id": getattr(entity, "id", getattr(entity, "name", "")),
        "name": getattr(entity, "name", getattr(entity, "type_name", "")),
        "type": getattr(entity, "type_name", entity.__class__.__name__),
        "source": source,
        "layer": getattr(entity, "layer_name", None),
        "location": _vector_to_data(box.center if box.valid else Vector3()),
        "signature": _entity_signature(entity),
        "geometry": _geometry_signature(entity),
        "metadata": {
            "visible": getattr(entity, "visible", True),
            "locked": getattr(entity, "locked", False),
            "display_mode": getattr(entity, "display_mode", ""),
        },
        "reference": getattr(entity, "model_id", ""),
    }


def _reference_snapshot(model):

    box = getattr(model.mesh_data, "bounding_box3d", BoundingBox3D())

    return {
        "id": getattr(model, "id", getattr(model, "name", "")),
        "name": getattr(model, "name", "Reference Model"),
        "type": "ReferenceModel",
        "source": "Reference",
        "layer": getattr(model, "group", ""),
        "location": _vector_to_data(box.center if box.valid else Vector3()),
        "signature": f"{model.reader_type}:{model.import_statistics.vertices}:{model.import_statistics.faces}",
        "geometry": {
            "vertices": model.import_statistics.vertices,
            "faces": model.import_statistics.faces,
        },
        "metadata": {
            "path": model.path,
            "status": model.status,
            "category": model.category,
            "group": model.group,
        },
        "reference": model.id,
    }


def _entity_signature(entity):

    mesh = getattr(entity, "mesh_data", None)
    box = getattr(entity, "bounding_box3d", BoundingBox3D())
    bounds = _box_signature(box)

    if mesh is not None:
        return f"mesh:{len(mesh.vertices)}:{len(mesh.faces)}:{bounds}"

    return f"{entity.__class__.__name__}:{len(entity.points())}:{len(entity.segments())}:{bounds}"


def _geometry_signature(entity):

    mesh = getattr(entity, "mesh_data", None)
    box = getattr(entity, "bounding_box3d", BoundingBox3D())
    bounds = _box_signature(box)

    if mesh is not None:
        return {"vertices": len(mesh.vertices), "faces": len(mesh.faces), "bounds": bounds}

    return {"points": len(entity.points()), "segments": len(entity.segments()), "bounds": bounds}


def _box_signature(box):

    if box is None or not getattr(box, "valid", False):
        return None

    return {
        "min": _rounded_vector(box.min),
        "max": _rounded_vector(box.max),
    }


def _rounded_vector(vector):

    return {
        "x": round(vector.x, 6),
        "y": round(vector.y, 6),
        "z": round(vector.z, 6),
    }


def _result(change_type, object_id, before, after, description=""):

    data = after or before or {}

    return CompareResult(
        change_type,
        object_id,
        data.get("name", change_type),
        before,
        after,
        description or f"{change_type}: {data.get('name', object_id)}",
        _snapshot_location(data),
    )


def _snapshot_location(snapshot):

    return _vector_from_data((snapshot or {}).get("location"))


def _snapshot_collection_location(snapshots):

    points = [
        _vector_from_data(item.get("location"))
        for item in list(snapshots or [])
        if item.get("location") is not None
    ]

    if not points:
        return Vector3()

    total = Vector3()

    for point in points:
        total = total + point

    return total * (1.0 / len(points))


def _count(results, change_type):

    return len([result for result in results if result.change_type == change_type])


def _timestamp():

    return datetime.now(timezone.utc).isoformat()


def _vector_to_data(vector):

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def _vector_from_data(data):

    data = data or {}

    return Vector3(data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))

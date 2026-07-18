from datetime import datetime, timezone
from uuid import uuid4

from engine.geometry import BoundingBox3D, Vector3


ISSUE_STATUSES = ("Open", "In Progress", "Resolved", "Closed", "Archived")
ISSUE_PRIORITIES = ("Low", "Normal", "High", "Critical")
ISSUE_CATEGORIES = ("General", "Coordination", "Design", "Safety", "Fabrication", "Review")
SESSION_STATUSES = ("Active", "Archived", "Completed")


class Participant:
    """Local review-session participant metadata."""

    def __init__(self, name, role="Reviewer", email=""):

        self.id = str(uuid4())
        self.name = str(name)
        self.role = role
        self.email = email

    def to_dict(self):
        """Return JSON-safe participant data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create participant metadata from persisted data."""

        data = data or {}
        participant = Participant(
            data.get("name", "Participant"),
            data.get("role", "Reviewer"),
            data.get("email", ""),
        )
        participant.id = data.get("id", participant.id)

        return participant


class SessionMetadata:
    """Review session metadata future-ready for offline/online workflows."""

    def __init__(self, owner="", created_at=None, modified_at=None):

        self.owner = owner
        self.created_at = created_at or _timestamp()
        self.modified_at = modified_at or self.created_at

    def touch(self):
        """Update modified time."""

        self.modified_at = _timestamp()

    def to_dict(self):
        """Return JSON-safe metadata."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create metadata from persisted data."""

        data = data or {}

        return SessionMetadata(
            data.get("owner", ""),
            data.get("created_at"),
            data.get("modified_at"),
        )


class SessionSettings:
    """Local review session settings without networking behavior."""

    def __init__(self, visible=True, show_issue_markers=True, show_session_overlay=True):

        self.visible = bool(visible)
        self.show_issue_markers = bool(show_issue_markers)
        self.show_session_overlay = bool(show_session_overlay)

    def to_dict(self):
        """Return JSON-safe settings."""

        return dict(self.__dict__)

    def from_dict(self, data):
        """Restore settings."""

        for key, value in (data or {}).items():
            if hasattr(self, key):
                setattr(self, key, value)


class Session:
    """Persistent local review session."""

    def __init__(self, name="Review Session", owner="", notes=""):

        self.id = str(uuid4())
        self.name = str(name)
        self.metadata = SessionMetadata(owner)
        self.settings = SessionSettings()
        self.participants = []
        self.status = "Active"
        self.notes = notes
        self.tags = []
        self.history = []

    def add_participant(self, participant):
        """Add a session participant."""

        if participant not in self.participants:
            self.participants.append(participant)
            self.add_history("participant_added", participant.name)

    def add_note(self, note, author=""):
        """Append a session note."""

        self.notes = f"{self.notes}\n{note}".strip()
        self.add_history("note", note, author)

    def add_history(self, action, detail="", author=""):
        """Append a session history record."""

        self.history.append({
            "action": action,
            "detail": detail,
            "author": author,
            "timestamp": _timestamp(),
        })
        self.metadata.touch()

    def archive(self):
        """Archive this session."""

        self.status = "Archived"
        self.add_history("archived")

    def restore(self):
        """Restore this session."""

        self.status = "Active"
        self.add_history("restored")

    def duplicate(self, name=None):
        """Return a detached duplicated session."""

        duplicate = Session(name or f"{self.name} Copy", self.metadata.owner, self.notes)
        duplicate.settings.from_dict(self.settings.to_dict())
        duplicate.participants = [Participant.from_dict(item.to_dict()) for item in self.participants]
        duplicate.tags = list(self.tags)
        duplicate.add_history("duplicated", self.name)

        return duplicate

    def to_dict(self):
        """Return JSON-safe session data."""

        return {
            "id": self.id,
            "name": self.name,
            "metadata": self.metadata.to_dict(),
            "settings": self.settings.to_dict(),
            "participants": [participant.to_dict() for participant in self.participants],
            "status": self.status,
            "notes": self.notes,
            "tags": list(self.tags),
            "history": list(self.history),
        }

    @staticmethod
    def from_dict(data):
        """Create a session from persisted data."""

        data = data or {}
        session = Session(data.get("name", "Review Session"), notes=data.get("notes", ""))
        session.id = data.get("id", session.id)
        session.metadata = SessionMetadata.from_dict(data.get("metadata", {}))
        session.settings.from_dict(data.get("settings", {}))
        session.participants = [
            Participant.from_dict(item)
            for item in data.get("participants", [])
        ]
        session.status = data.get("status", "Active")
        session.tags = list(data.get("tags", []))
        session.history = list(data.get("history", []))

        return session


class CollaborationManager:
    """Workspace-owned local collaboration and review-session manager."""

    def __init__(self):

        self.sessions = []
        self.active = None
        self.settings = SessionSettings()

    def create_session(self, name="Review Session", owner="", notes=""):
        """Create a local review session."""

        return self.add(Session(self._unique_name(name), owner, notes))

    def add(self, session):
        """Store a session."""

        if session not in self.sessions:
            session.name = self._unique_name(session.name, session)
            self.sessions.append(session)

        if self.active is None:
            self.active = session

        return session

    def rename(self, session, name):
        """Rename a session."""

        target = self.get(session)

        if target is None:
            return False

        target.name = self._unique_name(name, target)
        target.add_history("renamed", target.name)

        return True

    def archive(self, session):
        """Archive a session."""

        target = self.get(session)

        if target is None:
            return False

        target.archive()

        return True

    def restore(self, session):
        """Restore an archived session."""

        target = self.get(session)

        if target is None:
            return False

        target.restore()

        return True

    def duplicate(self, session, name=None):
        """Duplicate a session."""

        target = self.get(session)

        if target is None:
            return None

        return self.add(target.duplicate(self._unique_name(name or f"{target.name} Copy")))

    def search(self, text):
        """Search sessions by name, notes or tags."""

        query = str(text or "").lower()

        return [
            session for session in self.sessions
            if (
                query in session.name.lower() or
                query in session.notes.lower() or
                any(query in tag.lower() for tag in session.tags)
            )
        ]

    def filter(self, status=None, tag=None):
        """Filter sessions by status and tag."""

        return [
            session for session in self.sessions
            if (
                (status is None or session.status == status) and
                (tag is None or tag in session.tags)
            )
        ]

    def get(self, session):
        """Return session by object, id or name."""

        if isinstance(session, Session):
            return session if session in self.sessions else None

        for item in self.sessions:
            if item.id == session or item.name == session:
                return item

        return None

    def to_dict(self):
        """Return JSON-safe collaboration data."""

        return {
            "active": getattr(self.active, "id", None),
            "settings": self.settings.to_dict(),
            "sessions": [session.to_dict() for session in self.sessions],
        }

    def from_dict(self, data):
        """Restore collaboration data."""

        data = data or {}
        self.settings.from_dict(data.get("settings", {}))
        self.sessions = [
            Session.from_dict(item)
            for item in data.get("sessions", [])
        ]
        self.active = self.get(data.get("active")) or (self.sessions[0] if self.sessions else None)

    def _unique_name(self, name, current=None):

        base = str(name or "Review Session").strip() or "Review Session"
        names = {
            session.name for session in self.sessions
            if session is not current
        }

        if base not in names:
            return base

        index = 1

        while f"{base} {index}" in names:
            index += 1

        return f"{base} {index}"


class Issue:
    """Persistent selectable 3D issue marker."""

    type_name = "Issue"
    is_3d = True
    is_issue = True

    def __init__(
        self,
        title="Issue",
        description="",
        position=None,
        status="Open",
        priority="Normal",
        category="General",
        reporter="",
        assignee="",
    ):

        self.id = str(uuid4())
        self.name = str(title)
        self.title = str(title)
        self.description = description
        self.position = position.copy() if position is not None else Vector3()
        self.status = status if status in ISSUE_STATUSES else "Open"
        self.priority = priority if priority in ISSUE_PRIORITIES else "Normal"
        self.category = category if category in ISSUE_CATEGORIES else category
        self.reporter = reporter
        self.assignee = assignee
        self.created_date = _timestamp()
        self.modified_date = self.created_date
        self.resolved_date = None
        self.due_date = None
        self.linked_entity = None
        self.linked_annotation = None
        self.linked_review_item = None
        self.attachments = []
        self.tags = []
        self.visible = True
        self.locked = False
        self.selected = False
        self.hovered = False
        self.layer = None
        self.layer_id = None
        self.layer_name = None
        self.color = "#ff7043"

    @property
    def bounding_box3d(self):
        """Return issue marker bounds."""

        box = BoundingBox3D()
        pad = 4.0
        box.add(self.position - Vector3(pad, pad, pad))
        box.add(self.position + Vector3(pad, pad, pad))

        return box

    @property
    def display_color(self):
        """Return issue marker display color."""

        if self.status == "Resolved":
            return "#66bb6a"

        if self.priority == "Critical":
            return "#ef5350"

        return self.color

    def points(self):
        """Return issue marker points."""

        return [self.position]

    def segments(self):
        """Return issue marker crosshair segments."""

        size = 10.0

        return [
            (self.position - Vector3(size, 0.0, 0.0), self.position + Vector3(size, 0.0, 0.0)),
            (self.position - Vector3(0.0, size, 0.0), self.position + Vector3(0.0, size, 0.0)),
            (self.position - Vector3(0.0, 0.0, size), self.position + Vector3(0.0, 0.0, size)),
        ]

    def touch(self):
        """Update modification timestamp."""

        self.modified_date = _timestamp()

    def resolve(self):
        """Mark issue resolved."""

        self.status = "Resolved"
        self.resolved_date = _timestamp()
        self.touch()

    def reopen(self):
        """Reopen issue."""

        self.status = "Open"
        self.resolved_date = None
        self.touch()

    def to_dict(self):
        """Return JSON-safe issue data."""

        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "position": _vector_to_data(self.position),
            "status": self.status,
            "priority": self.priority,
            "category": self.category,
            "reporter": self.reporter,
            "assignee": self.assignee,
            "created_date": self.created_date,
            "modified_date": self.modified_date,
            "resolved_date": self.resolved_date,
            "due_date": self.due_date,
            "linked_entity": self.linked_entity,
            "linked_annotation": self.linked_annotation,
            "linked_review_item": self.linked_review_item,
            "attachments": list(self.attachments),
            "tags": list(self.tags),
            "visible": self.visible,
            "locked": self.locked,
            "selected": self.selected,
            "layer_name": self.layer_name,
            "color": self.color,
        }

    @staticmethod
    def from_dict(data):
        """Create an issue from persisted data."""

        data = data or {}
        issue = Issue(
            data.get("title", "Issue"),
            data.get("description", ""),
            _vector_from_data(data.get("position")),
            data.get("status", "Open"),
            data.get("priority", "Normal"),
            data.get("category", "General"),
            data.get("reporter", ""),
            data.get("assignee", ""),
        )
        issue.id = data.get("id", issue.id)
        issue.name = data.get("name", issue.title)
        issue.created_date = data.get("created_date", issue.created_date)
        issue.modified_date = data.get("modified_date", issue.modified_date)
        issue.resolved_date = data.get("resolved_date")
        issue.due_date = data.get("due_date")
        issue.linked_entity = data.get("linked_entity")
        issue.linked_annotation = data.get("linked_annotation")
        issue.linked_review_item = data.get("linked_review_item")
        issue.attachments = list(data.get("attachments", []))
        issue.tags = list(data.get("tags", []))
        issue.visible = bool(data.get("visible", True))
        issue.locked = bool(data.get("locked", False))
        issue.selected = bool(data.get("selected", False))
        issue.layer_name = data.get("layer_name")
        issue.color = data.get("color", issue.color)

        return issue


class IssueManager:
    """Workspace-owned issue tracking manager."""

    def __init__(self):

        self.issues = []
        self.visible = True

    def add(self, issue):
        """Store an issue."""

        if issue not in self.issues:
            self.issues.append(issue)

        return issue

    def remove(self, issue):
        """Remove an issue."""

        target = self.get(issue)

        if target is None:
            return False

        self.issues.remove(target)

        return True

    def create(self, title, position=None, **metadata):
        """Create an issue."""

        return self.add(Issue(title, position=position, **metadata))

    def visible_issues(self):
        """Return visible issues."""

        if not self.visible:
            return []

        return [
            issue for issue in self.issues
            if getattr(issue, "visible", True)
        ]

    def search(self, text):
        """Search issues by text, tags and metadata."""

        query = str(text or "").lower()

        return [
            issue for issue in self.issues
            if (
                query in issue.title.lower() or
                query in issue.description.lower() or
                query in issue.category.lower() or
                query in issue.reporter.lower() or
                query in issue.assignee.lower() or
                any(query in tag.lower() for tag in issue.tags)
            )
        ]

    def filter(self, status=None, priority=None, category=None, assignee=None, tag=None):
        """Filter issues by common review fields."""

        return [
            issue for issue in self.issues
            if (
                (status is None or issue.status == status) and
                (priority is None or issue.priority == priority) and
                (category is None or issue.category == category) and
                (assignee is None or issue.assignee == assignee) and
                (tag is None or tag in issue.tags)
            )
        ]

    def linked_to_annotation(self, annotation):
        """Return issues linked to an annotation."""

        annotation_id = getattr(annotation, "id", annotation)

        return [
            issue for issue in self.issues
            if issue.linked_annotation == annotation_id
        ]

    def get(self, issue):
        """Return issue by object, id or title."""

        if isinstance(issue, Issue):
            return issue if issue in self.issues else None

        for item in self.issues:
            if item.id == issue or item.title == issue or item.name == issue:
                return item

        return None

    def to_dict(self):
        """Return JSON-safe issue manager data."""

        return {
            "visible": self.visible,
            "issues": [issue.to_dict() for issue in self.issues],
        }

    def from_dict(self, data):
        """Restore issue manager data."""

        data = data or {}
        self.visible = bool(data.get("visible", True))
        self.issues = [
            Issue.from_dict(item)
            for item in data.get("issues", [])
        ]


def _timestamp():

    return datetime.now(timezone.utc).isoformat()


def _vector_to_data(vector):

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def _vector_from_data(data):

    data = data or {}

    return Vector3(data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))

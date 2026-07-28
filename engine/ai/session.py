from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def _timestamp():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AIMessage:
    """One persisted AI session message."""

    role: str
    content: str
    timestamp: str = field(default_factory=_timestamp)
    provider_id: str = ""
    task_id: str = ""

    def to_dict(self):
        """Return JSON-safe message state."""

        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data):
        """Restore a persisted message."""

        return cls(
            data.get("role", ""),
            data.get("content", ""),
            data.get("timestamp", _timestamp()),
            data.get("provider_id", ""),
            data.get("task_id", ""),
        )


@dataclass
class AISession:
    """Conversation session attached to workspace/project context."""

    name: str = "AI Session"
    id: str = field(default_factory=lambda: str(uuid4()))
    workspace_name: str = ""
    project_path: str = ""
    selection_ids: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    context: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_timestamp)
    updated_at: str = field(default_factory=_timestamp)

    def add_message(self, role, content, provider_id="", task_id=""):
        """Append a message to the session history."""

        message = AIMessage(role, content, provider_id=provider_id, task_id=task_id)
        self.messages.append(message)
        self.updated_at = _timestamp()
        return message

    def attach_workspace(self, workspace, project_path=""):
        """Attach session metadata to the active workspace."""

        self.workspace_name = getattr(workspace, "name", "")
        self.project_path = project_path or self.project_path
        selection = getattr(workspace, "selection", None)
        self.selection_ids = [
            getattr(item, "id", "") or getattr(item, "name", "")
            for item in getattr(selection, "selected", [])
        ] if selection is not None else []
        self.updated_at = _timestamp()

    def refresh_context(self, context):
        """Replace session context with a fresh Workspace-derived snapshot."""

        self.context = dict(context or {})
        self.updated_at = _timestamp()

    def to_dict(self):
        """Return JSON-safe session state."""

        return {
            "id": self.id,
            "name": self.name,
            "workspace_name": self.workspace_name,
            "project_path": self.project_path,
            "selection_ids": list(self.selection_ids),
            "messages": [message.to_dict() for message in self.messages],
            "context": dict(self.context),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data):
        """Restore a persisted session."""

        session = cls(data.get("name", "AI Session"), data.get("id") or str(uuid4()))
        session.workspace_name = data.get("workspace_name", "")
        session.project_path = data.get("project_path", "")
        session.selection_ids = list(data.get("selection_ids", []))
        session.messages = [AIMessage.from_dict(item) for item in data.get("messages", [])]
        session.context = dict(data.get("context", {}))
        session.created_at = data.get("created_at", session.created_at)
        session.updated_at = data.get("updated_at", session.updated_at)
        return session


class AISessionStore:
    """Stores AI Studio conversation sessions."""

    def __init__(self):
        self.sessions = []
        self.active_session_id = ""

    def create(self, name="AI Session", workspace=None, project_path=""):
        """Create and activate a session."""

        session = AISession(name)
        if workspace is not None:
            session.attach_workspace(workspace, project_path)
        self.sessions.append(session)
        self.active_session_id = session.id
        return session

    def active(self):
        """Return the active session."""

        return self.session_for(self.active_session_id)

    def session_for(self, session_id):
        """Return a session by ID."""

        return next((session for session in self.sessions if session.id == session_id), None)

    def to_dict(self):
        """Return JSON-safe session store state."""

        return {
            "active_session_id": self.active_session_id,
            "sessions": [session.to_dict() for session in self.sessions],
        }

    def from_dict(self, data):
        """Restore session store state."""

        self.sessions = [AISession.from_dict(item) for item in data.get("sessions", [])]
        self.active_session_id = data.get("active_session_id", "")

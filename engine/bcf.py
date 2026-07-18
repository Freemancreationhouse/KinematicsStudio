import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from engine.geometry import Vector3


class BCFMetadata:
    """Persistent BCF project metadata and compatibility settings."""

    def __init__(self, version="2.1", author="", source="Kinematics Studio V2"):

        self.version = version
        self.author = author
        self.source = source
        self.created_at = _timestamp()
        self.import_settings = {}
        self.export_settings = {}
        self.attachments = []

    def to_dict(self):
        """Return JSON-safe metadata."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create metadata from persisted data."""

        data = data or {}
        metadata = BCFMetadata(
            data.get("version", "2.1"),
            data.get("author", ""),
            data.get("source", "Kinematics Studio V2"),
        )
        metadata.created_at = data.get("created_at", metadata.created_at)
        metadata.import_settings = dict(data.get("import_settings", {}))
        metadata.export_settings = dict(data.get("export_settings", {}))
        metadata.attachments = list(data.get("attachments", []))

        return metadata


class BCFViewpoint:
    """Persistent BCF camera viewpoint."""

    def __init__(self, name="Viewpoint", position=None, target=None, up=None):

        self.id = str(uuid4())
        self.name = name
        self.position = position or Vector3(0.0, -250.0, 160.0)
        self.target = target or Vector3()
        self.up = up or Vector3(0.0, 0.0, 1.0)
        self.camera_type = "Perspective"

    def apply_to_camera(self, camera):
        """Restore this viewpoint to a camera-like object."""

        if camera is None:
            return

        if hasattr(camera, "position"):
            camera.position = self.position
        if hasattr(camera, "target"):
            camera.target = self.target
        if hasattr(camera, "up"):
            camera.up = self.up

    def to_dict(self):
        """Return JSON-safe viewpoint data."""

        return {
            "id": self.id,
            "name": self.name,
            "position": _vector_to_data(self.position),
            "target": _vector_to_data(self.target),
            "up": _vector_to_data(self.up),
            "camera_type": self.camera_type,
        }

    @staticmethod
    def from_dict(data):
        """Create a viewpoint from persisted data."""

        data = data or {}
        viewpoint = BCFViewpoint(
            data.get("name", "Viewpoint"),
            _vector_from_data(data.get("position")),
            _vector_from_data(data.get("target")),
            _vector_from_data(data.get("up", {"z": 1.0})),
        )
        viewpoint.id = data.get("id", viewpoint.id)
        viewpoint.camera_type = data.get("camera_type", "Perspective")

        return viewpoint


class BCFComment:
    """Persistent BCF topic comment."""

    def __init__(self, text="", author="", status="Open"):

        self.id = str(uuid4())
        self.text = text
        self.author = author
        self.status = status
        self.created_at = _timestamp()

    def to_dict(self):
        """Return JSON-safe comment data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create a comment from persisted data."""

        data = data or {}
        comment = BCFComment(
            data.get("text", ""),
            data.get("author", ""),
            data.get("status", "Open"),
        )
        comment.id = data.get("id", comment.id)
        comment.created_at = data.get("created_at", comment.created_at)

        return comment


class BCFSnapshot:
    """Persistent BCF snapshot placeholder and overlay metadata."""

    def __init__(self, name="Snapshot", image_path="", overlay=True):

        self.id = str(uuid4())
        self.name = name
        self.image_path = image_path
        self.overlay = bool(overlay)
        self.created_at = _timestamp()

    def to_dict(self):
        """Return JSON-safe snapshot data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create a snapshot from persisted data."""

        data = data or {}
        snapshot = BCFSnapshot(
            data.get("name", "Snapshot"),
            data.get("image_path", ""),
            data.get("overlay", True),
        )
        snapshot.id = data.get("id", snapshot.id)
        snapshot.created_at = data.get("created_at", snapshot.created_at)

        return snapshot


class BCFTopic:
    """Persistent BCF coordination topic linked to workspace objects."""

    type_name = "BCFTopic"
    is_3d = True
    is_bcf = True

    def __init__(self, title="BCF Topic", description="", topic_type="Issue", status="Open"):

        self.id = str(uuid4())
        self.name = title
        self.title = title
        self.description = description
        self.topic_type = topic_type
        self.status = status
        self.priority = "Normal"
        self.assignee = ""
        self.labels = []
        self.created_at = _timestamp()
        self.modified_at = self.created_at
        self.linked_issue_id = ""
        self.linked_review_id = ""
        self.linked_clash_id = ""
        self.linked_reference_id = ""
        self.selection_ids = []
        self.viewpoints = []
        self.comments = []
        self.snapshots = []
        self.visible = True
        self.locked = False
        self.selected = False
        self.hovered = False
        self.color = "#29b6f6"

    @property
    def display_color(self):
        """Return topic display color."""

        return self.color

    @property
    def location(self):
        """Return a representative display location."""

        if self.viewpoints:
            return self.viewpoints[0].target

        return Vector3()

    @property
    def bounding_box3d(self):
        """Return a small display bounds box."""

        from engine.geometry import BoundingBox3D

        box = BoundingBox3D()
        pad = 6.0
        box.add(self.location - Vector3(pad, pad, pad))
        box.add(self.location + Vector3(pad, pad, pad))

        return box

    def points(self):
        """Return representative topic points."""

        return [self.location]

    def segments(self):
        """Return marker segments."""

        pad = 6.0

        return [
            (self.location - Vector3(pad, 0.0, 0.0), self.location + Vector3(pad, 0.0, 0.0)),
            (self.location - Vector3(0.0, pad, 0.0), self.location + Vector3(0.0, pad, 0.0)),
        ]

    def add_comment(self, text, author=""):
        """Append a BCF comment."""

        comment = text if isinstance(text, BCFComment) else BCFComment(text, author, self.status)
        self.comments.append(comment)
        self.modified_at = _timestamp()

        return comment

    def add_viewpoint(self, viewpoint):
        """Store a viewpoint."""

        self.viewpoints.append(viewpoint)
        self.modified_at = _timestamp()

        return viewpoint

    def add_snapshot(self, snapshot):
        """Store a snapshot placeholder."""

        self.snapshots.append(snapshot)
        self.modified_at = _timestamp()

        return snapshot

    def to_dict(self):
        """Return JSON-safe topic data."""

        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "topic_type": self.topic_type,
            "status": self.status,
            "priority": self.priority,
            "assignee": self.assignee,
            "labels": list(self.labels),
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "linked_issue_id": self.linked_issue_id,
            "linked_review_id": self.linked_review_id,
            "linked_clash_id": self.linked_clash_id,
            "linked_reference_id": self.linked_reference_id,
            "selection_ids": list(self.selection_ids),
            "viewpoints": [viewpoint.to_dict() for viewpoint in self.viewpoints],
            "comments": [comment.to_dict() for comment in self.comments],
            "snapshots": [snapshot.to_dict() for snapshot in self.snapshots],
            "visible": self.visible,
            "locked": self.locked,
            "selected": self.selected,
            "color": self.color,
        }

    @staticmethod
    def from_dict(data):
        """Create a topic from persisted data."""

        data = data or {}
        topic = BCFTopic(
            data.get("title", "BCF Topic"),
            data.get("description", ""),
            data.get("topic_type", "Issue"),
            data.get("status", "Open"),
        )
        topic.id = data.get("id", topic.id)
        topic.name = data.get("name", topic.title)
        topic.priority = data.get("priority", "Normal")
        topic.assignee = data.get("assignee", "")
        topic.labels = list(data.get("labels", []))
        topic.created_at = data.get("created_at", topic.created_at)
        topic.modified_at = data.get("modified_at", topic.modified_at)
        topic.linked_issue_id = data.get("linked_issue_id", "")
        topic.linked_review_id = data.get("linked_review_id", "")
        topic.linked_clash_id = data.get("linked_clash_id", "")
        topic.linked_reference_id = data.get("linked_reference_id", "")
        topic.selection_ids = list(data.get("selection_ids", []))
        topic.viewpoints = [BCFViewpoint.from_dict(item) for item in data.get("viewpoints", [])]
        topic.comments = [BCFComment.from_dict(item) for item in data.get("comments", [])]
        topic.snapshots = [BCFSnapshot.from_dict(item) for item in data.get("snapshots", [])]
        topic.visible = bool(data.get("visible", True))
        topic.locked = bool(data.get("locked", False))
        topic.selected = bool(data.get("selected", False))
        topic.color = data.get("color", topic.color)

        return topic


class BCFProject:
    """Persistent BCF project containing coordination topics."""

    def __init__(self, name="BCF Project"):

        self.id = str(uuid4())
        self.name = name
        self.metadata = BCFMetadata()
        self.topics = []

    def add_topic(self, topic):
        """Store a topic in this project."""

        if topic not in self.topics:
            self.topics.append(topic)

        return topic

    def to_dict(self):
        """Return JSON-safe project data."""

        return {
            "id": self.id,
            "name": self.name,
            "metadata": self.metadata.to_dict(),
            "topics": [topic.to_dict() for topic in self.topics],
        }

    @staticmethod
    def from_dict(data):
        """Create a BCF project from persisted data."""

        data = data or {}
        project = BCFProject(data.get("name", "BCF Project"))
        project.id = data.get("id", project.id)
        project.metadata = BCFMetadata.from_dict(data.get("metadata", {}))
        project.topics = [BCFTopic.from_dict(item) for item in data.get("topics", [])]

        return project


class BCFManager:
    """Workspace-owned BCF coordination exchange manager."""

    def __init__(self):

        self.projects = []
        self.active_project_id = None
        self.visible = True
        self.settings = {
            "import_version": "2.1",
            "export_version": "2.1",
            "include_snapshots": True,
            "include_viewpoints": True,
        }

    @property
    def active_project(self):
        """Return the active BCF project."""

        if not self.projects:
            project = BCFProject()
            self.add_project(project)
            return project

        return self.get_project(self.active_project_id) or self.projects[0]

    def add_project(self, project):
        """Store a BCF project."""

        if project not in self.projects:
            self.projects.append(project)

        if self.active_project_id is None:
            self.active_project_id = project.id

        return project

    def remove_project(self, project):
        """Remove a BCF project."""

        target = self.get_project(project)

        if target is None:
            return False

        self.projects.remove(target)
        if self.active_project_id == target.id:
            self.active_project_id = self.projects[0].id if self.projects else None

        return True

    def add_topic(self, topic, project=None):
        """Store a topic in the selected project."""

        target_project = self.get_project(project) if project is not None else self.active_project
        if topic not in target_project.topics:
            target_project.topics.append(topic)

        return topic

    def remove_topic(self, topic):
        """Remove a topic from any BCF project."""

        target = self.get_topic(topic)

        if target is None:
            return False

        for project in self.projects:
            if target in project.topics:
                project.topics.remove(target)
                return True

        return False

    def topics(self):
        """Return all BCF topics."""

        return [
            topic
            for project in self.projects
            for topic in project.topics
        ]

    def visible_topics(self):
        """Return visible BCF topics."""

        if not self.visible:
            return []

        return [topic for topic in self.topics() if topic.visible]

    def create_topic_from_clash(self, clash, camera=None):
        """Create a BCF topic linked to a clash."""

        topic = BCFTopic(getattr(clash, "name", "Clash Topic"), getattr(clash, "description", ""), "Clash", getattr(clash, "status", "Open"))
        topic.linked_clash_id = getattr(clash, "id", "")
        topic.selection_ids = [topic.linked_clash_id] if topic.linked_clash_id else []
        topic.add_viewpoint(_viewpoint_from_camera(camera, getattr(clash, "location", Vector3())))
        topic.add_snapshot(BCFSnapshot(f"{topic.title} Snapshot"))

        return self.add_topic(topic)

    def create_topic_from_issue(self, issue, camera=None):
        """Create a BCF topic linked to an issue."""

        topic = BCFTopic(getattr(issue, "title", "Issue Topic"), getattr(issue, "description", ""), "Issue", getattr(issue, "status", "Open"))
        topic.linked_issue_id = getattr(issue, "id", "")
        topic.selection_ids = [topic.linked_issue_id] if topic.linked_issue_id else []
        topic.add_viewpoint(_viewpoint_from_camera(camera, getattr(issue, "position", Vector3())))

        return self.add_topic(topic)

    def create_topic_from_review(self, review, camera=None):
        """Create a BCF topic linked to a review item."""

        topic = BCFTopic(getattr(review, "title", "Review Topic"), "", "Review", getattr(review, "status", "Open"))
        topic.linked_review_id = getattr(review, "id", "")
        topic.add_viewpoint(_viewpoint_from_camera(camera))

        return self.add_topic(topic)

    def create_topic_from_reference(self, reference, camera=None):
        """Create a BCF topic linked to a reference instance."""

        topic = BCFTopic(getattr(reference, "name", "Reference Topic"), "", "Reference", "Open")
        topic.linked_reference_id = getattr(reference, "id", "")
        topic.selection_ids = [topic.linked_reference_id] if topic.linked_reference_id else []
        topic.add_viewpoint(_viewpoint_from_camera(camera, getattr(getattr(reference, "transform", None), "position", Vector3())))

        return self.add_topic(topic)

    def sync_selection(self, workspace, topic):
        """Synchronize workspace selection from a topic."""

        target = self.get_topic(topic)

        if target is None:
            return []

        selected = []
        for entity in _selectable_bcf_entities(workspace):
            if getattr(entity, "id", None) in target.selection_ids:
                selected.append(entity)

        if selected:
            workspace.selection.select_many(selected)

        return selected

    def restore_viewpoint(self, topic, camera):
        """Restore the first topic viewpoint to a camera."""

        target = self.get_topic(topic)

        if target is None or not target.viewpoints:
            return None

        target.viewpoints[0].apply_to_camera(camera)

        return target.viewpoints[0]

    def export_bcf(self, path, project=None):
        """Export one BCF project to a JSON-based BCF foundation file."""

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        project_data = (self.get_project(project) if project is not None else self.active_project).to_dict()
        target.write_text(json.dumps({"bcf": project_data}, indent=2), encoding="utf-8")

        return target

    def import_bcf(self, path):
        """Import one BCF project from a JSON-based BCF foundation file."""

        data = json.loads(Path(path).read_text(encoding="utf-8"))
        project = BCFProject.from_dict(data.get("bcf", data))
        self.add_project(project)

        return project

    def get_project(self, project):
        """Return project by object, id or name."""

        if isinstance(project, BCFProject):
            return project if project in self.projects else None

        for item in self.projects:
            if item.id == project or item.name == project:
                return item

        return None

    def get_topic(self, topic):
        """Return topic by object, id or title."""

        if isinstance(topic, BCFTopic):
            return topic if topic in self.topics() else None

        for item in self.topics():
            if item.id == topic or item.title == topic or item.name == topic:
                return item

        return None

    def project_for_topic(self, topic):
        """Return the BCF project that owns a topic."""

        target = self.get_topic(topic)

        if target is None:
            return None

        for project in self.projects:
            if target in project.topics:
                return project

        return None

    def to_dict(self):
        """Return JSON-safe manager data."""

        return {
            "visible": self.visible,
            "settings": dict(self.settings),
            "active_project_id": self.active_project_id,
            "projects": [project.to_dict() for project in self.projects],
        }

    def from_dict(self, data):
        """Restore manager data."""

        data = data or {}
        self.visible = bool(data.get("visible", True))
        self.settings.update(data.get("settings", {}))
        self.projects = [BCFProject.from_dict(item) for item in data.get("projects", [])]
        self.active_project_id = data.get("active_project_id")


def _viewpoint_from_camera(camera, target=None):

    return BCFViewpoint(
        position=getattr(camera, "position", Vector3(0.0, -250.0, 160.0)),
        target=target or getattr(camera, "target", Vector3()),
        up=getattr(camera, "up", Vector3(0.0, 0.0, 1.0)),
    )


def _selectable_bcf_entities(workspace):

    entities = []
    entities.extend(getattr(workspace.clash_manager, "results", []))
    entities.extend(getattr(workspace.issue_manager, "issues", []))
    entities.extend(getattr(workspace.reference_manager, "instances", []))

    return entities


def _timestamp():

    return datetime.now(timezone.utc).isoformat()


def _vector_to_data(vector):

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def _vector_from_data(data):

    data = data or {}

    return Vector3(data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))

from datetime import datetime, timezone
from uuid import uuid4

from engine.geometry import BoundingBox3D, Vector3


MARKUP_TYPES = (
    "Text Note",
    "Callout",
    "Arrow",
    "Cloud",
    "Highlight",
    "Freehand Sketch",
    "Marker",
    "Pinned Note",
    "Revision Marker",
    "Review Tag",
)


class Annotation3D:
    """Persistent selectable 3D annotation and markup entity."""

    type_name = "Annotation3D"
    is_3d = True
    is_annotation3d = True

    def __init__(
        self,
        annotation_type="Text Note",
        text="",
        points=None,
        screen_space=False,
        name=None,
        color="#ffcc80",
    ):

        self.id = str(uuid4())
        self.name = name or annotation_type
        self.annotation_type = annotation_type
        self.text = text
        self.points = [point.copy() for point in (points or [Vector3()])]
        self.screen_space = bool(screen_space)
        self.visible = True
        self.locked = False
        self.selected = False
        self.hovered = False
        self.layer = None
        self.layer_id = None
        self.layer_name = None
        self.color = color
        self.author = ""
        self.created_at = _timestamp()

    # --------------------------------

    @property
    def bounding_box3d(self):
        """Return annotation bounds."""

        box = BoundingBox3D()

        for point in self.points:
            box.add(point)

        return box

    # --------------------------------

    @property
    def display_color(self):
        """Return annotation display color."""

        return self.color or "#ffcc80"

    # --------------------------------

    def segments(self):
        """Return markup line graphics."""

        if len(self.points) < 2:
            return []

        if self.annotation_type == "Cloud" and len(self.points) > 2:
            return list(zip(self.points, self.points[1:] + self.points[:1]))

        return list(zip(self.points, self.points[1:]))

    # --------------------------------

    def representative_points(self):
        """Return annotation marker points."""

        return list(self.points)

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe annotation data."""

        return {
            "id": self.id,
            "name": self.name,
            "annotation_type": self.annotation_type,
            "text": self.text,
            "points": [_vector_to_data(point) for point in self.points],
            "screen_space": self.screen_space,
            "visible": self.visible,
            "locked": self.locked,
            "selected": self.selected,
            "layer_name": self.layer_name,
            "color": self.color,
            "author": self.author,
            "created_at": self.created_at,
        }

    # --------------------------------

    @staticmethod
    def from_dict(data):
        """Create an annotation from persisted data."""

        data = data or {}
        annotation = Annotation3D(
            data.get("annotation_type", "Text Note"),
            data.get("text", ""),
            [_vector_from_data(point) for point in data.get("points", [])],
            data.get("screen_space", False),
            data.get("name"),
            data.get("color", "#ffcc80"),
        )
        annotation.id = data.get("id", annotation.id)
        annotation.visible = bool(data.get("visible", True))
        annotation.locked = bool(data.get("locked", False))
        annotation.selected = bool(data.get("selected", False))
        annotation.layer_name = data.get("layer_name")
        annotation.author = data.get("author", "")
        annotation.created_at = data.get("created_at", annotation.created_at)

        return annotation


class AnnotationManager3D:
    """Workspace-owned 3D annotation and markup manager."""

    def __init__(self):

        self.annotations = []
        self.visible = True

    # --------------------------------

    def add(self, annotation):
        """Store an annotation."""

        if annotation not in self.annotations:
            self.annotations.append(annotation)

        return annotation

    # --------------------------------

    def remove(self, annotation):
        """Remove an annotation."""

        target = self.get(annotation)

        if target is None:
            return False

        self.annotations.remove(target)

        return True

    # --------------------------------

    def create(self, annotation_type, text="", points=None, screen_space=False, name=None):
        """Create and store a typed annotation/markup."""

        return self.add(Annotation3D(annotation_type, text, points, screen_space, name))

    # --------------------------------

    def text_note(self, text, point, screen_space=False):
        """Create a text note annotation."""

        return self.create("Text Note", text, [point], screen_space)

    # --------------------------------

    def callout(self, text, points):
        """Create a callout annotation."""

        return self.create("Callout", text, points)

    # --------------------------------

    def arrow(self, points):
        """Create an arrow markup."""

        return self.create("Arrow", "", points)

    # --------------------------------

    def cloud(self, points):
        """Create a cloud markup."""

        return self.create("Cloud", "", points)

    # --------------------------------

    def highlight(self, points):
        """Create a highlight markup."""

        return self.create("Highlight", "", points)

    # --------------------------------

    def freehand_sketch(self, points):
        """Create a freehand sketch markup."""

        return self.create("Freehand Sketch", "", points)

    # --------------------------------

    def marker(self, text, point):
        """Create a marker annotation."""

        return self.create("Marker", text, [point])

    # --------------------------------

    def pinned_note(self, text, point):
        """Create a pinned note annotation."""

        return self.create("Pinned Note", text, [point])

    # --------------------------------

    def revision_marker(self, text, point):
        """Create a revision marker."""

        return self.create("Revision Marker", text, [point])

    # --------------------------------

    def review_tag(self, text, point):
        """Create a review tag."""

        return self.create("Review Tag", text, [point])

    # --------------------------------

    def visible_annotations(self):
        """Return visible annotations."""

        if not self.visible:
            return []

        return [
            annotation for annotation in self.annotations
            if getattr(annotation, "visible", True)
        ]

    # --------------------------------

    def get(self, annotation):
        """Return annotation by object, id or name."""

        if isinstance(annotation, Annotation3D):
            return annotation if annotation in self.annotations else None

        for item in self.annotations:
            if item.id == annotation or item.name == annotation:
                return item

        return None

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe manager data."""

        return {
            "visible": self.visible,
            "annotations": [annotation.to_dict() for annotation in self.annotations],
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore annotation manager data."""

        data = data or {}
        self.visible = bool(data.get("visible", True))
        self.annotations = [
            Annotation3D.from_dict(item)
            for item in data.get("annotations", [])
        ]


class ReviewItem:
    """Persistent review item linked to one or more annotations."""

    def __init__(
        self,
        title="Review Item",
        status="Open",
        priority="Normal",
        author="",
        category="General",
        comments=None,
        annotation_ids=None,
    ):

        self.id = str(uuid4())
        self.title = str(title)
        self.status = status
        self.priority = priority
        self.author = author
        self.timestamp = _timestamp()
        self.resolved = False
        self.category = category
        self.comments = list(comments or [])
        self.annotation_ids = list(annotation_ids or [])

    # --------------------------------

    def add_comment(self, comment, author=""):
        """Append a review comment."""

        self.comments.append({
            "author": author,
            "text": comment,
            "timestamp": _timestamp(),
        })

    # --------------------------------

    def link_annotation(self, annotation):
        """Link an annotation by id."""

        annotation_id = getattr(annotation, "id", annotation)

        if annotation_id not in self.annotation_ids:
            self.annotation_ids.append(annotation_id)

    # --------------------------------

    def set_resolved(self, resolved=True):
        """Set resolved state and status."""

        self.resolved = bool(resolved)
        self.status = "Resolved" if self.resolved else "Open"

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe review item data."""

        return dict(self.__dict__)

    # --------------------------------

    @staticmethod
    def from_dict(data):
        """Create a review item from persisted data."""

        data = data or {}
        item = ReviewItem(
            data.get("title", "Review Item"),
            data.get("status", "Open"),
            data.get("priority", "Normal"),
            data.get("author", ""),
            data.get("category", "General"),
            data.get("comments", []),
            data.get("annotation_ids", []),
        )
        item.id = data.get("id", item.id)
        item.timestamp = data.get("timestamp", item.timestamp)
        item.resolved = bool(data.get("resolved", False))

        return item


class ReviewManager:
    """Workspace-owned review item manager."""

    def __init__(self):

        self.items = []
        self.visible = True

    # --------------------------------

    def add(self, item):
        """Store a review item."""

        if item not in self.items:
            self.items.append(item)

        return item

    # --------------------------------

    def remove(self, item):
        """Remove a review item."""

        target = self.get(item)

        if target is None:
            return False

        self.items.remove(target)

        return True

    # --------------------------------

    def create(self, title, annotation=None, **metadata):
        """Create a review item and optionally link an annotation."""

        item = ReviewItem(title, **metadata)

        if annotation is not None:
            item.link_annotation(annotation)

        return self.add(item)

    # --------------------------------

    def unresolved(self):
        """Return unresolved review items."""

        return [
            item for item in self.items
            if not item.resolved
        ]

    # --------------------------------

    def linked_to(self, annotation):
        """Return review items linked to an annotation."""

        annotation_id = getattr(annotation, "id", annotation)

        return [
            item for item in self.items
            if annotation_id in item.annotation_ids
        ]

    # --------------------------------

    def get(self, item):
        """Return review item by object, id or title."""

        if isinstance(item, ReviewItem):
            return item if item in self.items else None

        for review_item in self.items:
            if review_item.id == item or review_item.title == item:
                return review_item

        return None

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe review manager data."""

        return {
            "visible": self.visible,
            "items": [item.to_dict() for item in self.items],
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore review manager data."""

        data = data or {}
        self.visible = bool(data.get("visible", True))
        self.items = [
            ReviewItem.from_dict(item)
            for item in data.get("items", [])
        ]


def _timestamp():

    return datetime.now(timezone.utc).isoformat()


def _vector_to_data(vector):

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def _vector_from_data(data):

    data = data or {}

    return Vector3(data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))

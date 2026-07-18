from engine.geometry import BoundingBox3D, Vector3


class SectionPlane:
    """Persistent 3D section plane used for clipping and analysis overlays."""

    type_name = "SectionPlane"
    is_3d = True
    is_section = True

    def __init__(
        self,
        name="Section Plane",
        origin=None,
        normal=None,
        size=400.0,
        visible=True,
        enabled=True,
        locked=False,
        color="#26c6da",
    ):

        self.name = str(name)
        self.origin = origin.copy() if origin is not None else Vector3()
        self.normal = (normal or Vector3(0.0, 0.0, 1.0)).normalized()
        self.size = float(size)
        self.visible = bool(visible)
        self.enabled = bool(enabled)
        self.locked = bool(locked)
        self.color = color
        self.selected = False
        self.hovered = False
        self.layer = None
        self.layer_id = None
        self.layer_name = None

    # --------------------------------

    @property
    def bounding_box3d(self):
        """Return section plane overlay bounds."""

        box = BoundingBox3D()

        for point in self.points():
            box.add(point)

        return box

    # --------------------------------

    @property
    def display_color(self):
        """Return display color resolved for rendering."""

        return self.color or "#26c6da"

    # --------------------------------

    def points(self):
        """Return section plane corner points."""

        x_axis, y_axis = self._basis()
        half = self.size * 0.5

        return [
            self.origin - x_axis * half - y_axis * half,
            self.origin + x_axis * half - y_axis * half,
            self.origin + x_axis * half + y_axis * half,
            self.origin - x_axis * half + y_axis * half,
        ]

    # --------------------------------

    def segments(self):
        """Return section plane wire segments."""

        points = self.points()

        return list(zip(points, points[1:] + points[:1]))

    # --------------------------------

    def signed_distance(self, point):
        """Return signed distance from a point to this section plane."""

        return (point - self.origin).dot(self.normal)

    # --------------------------------

    def normal_segment(self, length=None):
        """Return a short normal indicator segment."""

        value = float(length if length is not None else self.size * 0.25)

        return (self.origin, self.origin + self.normal * value)

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe section plane data."""

        return {
            "name": self.name,
            "origin": _vector_to_data(self.origin),
            "normal": _vector_to_data(self.normal),
            "size": self.size,
            "visible": self.visible,
            "enabled": self.enabled,
            "locked": self.locked,
            "selected": self.selected,
            "layer_name": self.layer_name,
            "color": self.color,
        }

    # --------------------------------

    @staticmethod
    def from_dict(data):
        """Create a section plane from persisted data."""

        data = data or {}
        plane = SectionPlane(
            data.get("name", "Section Plane"),
            _vector_from_data(data.get("origin")),
            _vector_from_data(data.get("normal") or {"z": 1.0}),
            data.get("size", 400.0),
            data.get("visible", True),
            data.get("enabled", True),
            data.get("locked", False),
            data.get("color", "#26c6da"),
        )
        plane.selected = bool(data.get("selected", False))
        plane.layer_name = data.get("layer_name")

        return plane

    # --------------------------------

    def _basis(self):

        reference = Vector3(0.0, 0.0, 1.0)

        if abs(self.normal.dot(reference)) > 0.95:
            reference = Vector3(0.0, 1.0, 0.0)

        x_axis = reference.cross(self.normal).normalized()
        y_axis = self.normal.cross(x_axis).normalized()

        return x_axis, y_axis


class ClippingSettings:
    """Workspace-owned clipping settings for 3D analysis visualization."""

    def __init__(self):

        self.global_enabled = True
        self.local_enabled = True
        self.plane_enabled = True
        self.box_enabled = False
        self.preview_enabled = True
        self.clip_toggle = True
        self.box_min = Vector3(-500.0, -500.0, -500.0)
        self.box_max = Vector3(500.0, 500.0, 500.0)

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe clipping settings."""

        return {
            "global_enabled": self.global_enabled,
            "local_enabled": self.local_enabled,
            "plane_enabled": self.plane_enabled,
            "box_enabled": self.box_enabled,
            "preview_enabled": self.preview_enabled,
            "clip_toggle": self.clip_toggle,
            "box_min": _vector_to_data(self.box_min),
            "box_max": _vector_to_data(self.box_max),
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore clipping settings."""

        data = data or {}
        self.global_enabled = bool(data.get("global_enabled", self.global_enabled))
        self.local_enabled = bool(data.get("local_enabled", self.local_enabled))
        self.plane_enabled = bool(data.get("plane_enabled", self.plane_enabled))
        self.box_enabled = bool(data.get("box_enabled", self.box_enabled))
        self.preview_enabled = bool(data.get("preview_enabled", self.preview_enabled))
        self.clip_toggle = bool(data.get("clip_toggle", self.clip_toggle))
        self.box_min = _vector_from_data(data.get("box_min")) or self.box_min
        self.box_max = _vector_from_data(data.get("box_max")) or self.box_max


class AnalysisDisplaySettings:
    """Display toggles for non-destructive 3D analysis overlays."""

    def __init__(self):

        self.bounding_box_overlay = True
        self.face_normals = False
        self.vertex_display = False
        self.wireframe_overlay = True
        self.edge_overlay = True
        self.back_faces = False
        self.object_bounds = True
        self.selection_bounds = True
        self.heatmap_enabled = False
        self.heatmap_mode = "Future-ready placeholder"

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe analysis settings."""

        return dict(self.__dict__)

    # --------------------------------

    def from_dict(self, data):
        """Restore analysis settings."""

        for key, value in (data or {}).items():
            if hasattr(self, key):
                setattr(self, key, value)


class SectionManager:
    """Workspace-owned section, clipping and analysis visualization manager."""

    def __init__(self):

        self.sections = []
        self.active = None
        self.clipping = ClippingSettings()
        self.analysis = AnalysisDisplaySettings()

    # --------------------------------

    def create(self, name="Section Plane", origin=None, normal=None, size=400.0):
        """Create and store a unique section plane."""

        section = SectionPlane(
            self._unique_name(name),
            origin,
            normal,
            size,
        )

        return self.add(section)

    # --------------------------------

    def add(self, section):
        """Store a section plane."""

        if section not in self.sections:
            section.name = self._unique_name(section.name, section)
            self.sections.append(section)

        if self.active is None:
            self.active = section

        return section

    # --------------------------------

    def remove(self, section):
        """Remove a section plane."""

        target = self.get(section)

        if target is None:
            return False

        self.sections.remove(target)

        if self.active is target:
            self.active = self.sections[0] if self.sections else None

        return True

    # --------------------------------

    def set_active(self, section):
        """Set active section by object or name."""

        target = self.get(section)

        if target is not None:
            self.active = target

        return self.active

    # --------------------------------

    def get(self, section):
        """Return section by object or name."""

        if isinstance(section, SectionPlane):
            return section if section in self.sections else None

        for item in self.sections:
            if item.name == section:
                return item

        return None

    # --------------------------------

    def names(self):
        """Return section names."""

        return [section.name for section in self.sections]

    # --------------------------------

    def visible_sections(self):
        """Return visible section planes."""

        return [
            section for section in self.sections
            if getattr(section, "visible", True)
        ]

    # --------------------------------

    def enabled_sections(self):
        """Return section planes that participate in clipping."""

        return [
            section for section in self.sections
            if getattr(section, "enabled", True)
        ]

    # --------------------------------

    def is_entity_visible(self, entity):
        """Return True when an entity survives current clipping settings."""

        if not self.clipping.clip_toggle or not self.clipping.global_enabled:
            return True

        box = getattr(entity, "bounding_box3d", None)

        if box is None or not box.valid:
            return True

        if self.clipping.box_enabled and not self._box_intersects_clip_box(box):
            return False

        if not self.clipping.plane_enabled:
            return True

        points = box.corners()

        for section in self.enabled_sections():
            if not any(section.signed_distance(point) >= 0.0 for point in points):
                return False

        return True

    # --------------------------------

    def overlay_bounds(self, entities):
        """Return object and selection bounds for analysis overlays."""

        object_bounds = []
        selection_bounds = []

        for entity in entities:
            box = getattr(entity, "bounding_box3d", None)

            if box is None or not box.valid:
                continue

            object_bounds.append(box)

            if getattr(entity, "selected", False):
                selection_bounds.append(box)

        return object_bounds, selection_bounds

    # --------------------------------

    def face_normal_segments(self, entity, length=30.0):
        """Return face-normal display segments for mesh-like entities."""

        triangles = getattr(entity, "triangles", lambda: [])()
        segments = []

        for triangle in triangles:
            if len(triangle) != 3:
                continue

            a, b, c = triangle
            center = (a + b + c) / 3.0
            normal = (b - a).cross(c - a).normalized()
            segments.append((center, center + normal * float(length)))

        return segments

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe section manager data."""

        return {
            "active": getattr(self.active, "name", None),
            "sections": [section.to_dict() for section in self.sections],
            "clipping": self.clipping.to_dict(),
            "analysis": self.analysis.to_dict(),
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore section manager data."""

        data = data or {}
        self.sections = [
            SectionPlane.from_dict(item)
            for item in data.get("sections", [])
        ]
        self.active = self.get(data.get("active")) or (self.sections[0] if self.sections else None)
        self.clipping.from_dict(data.get("clipping", {}))
        self.analysis.from_dict(data.get("analysis", {}))

    # --------------------------------

    def _box_intersects_clip_box(self, box):

        return not (
            box.max.x < self.clipping.box_min.x or
            box.min.x > self.clipping.box_max.x or
            box.max.y < self.clipping.box_min.y or
            box.min.y > self.clipping.box_max.y or
            box.max.z < self.clipping.box_min.z or
            box.min.z > self.clipping.box_max.z
        )

    # --------------------------------

    def _unique_name(self, name, current=None):

        base = str(name or "Section Plane").strip() or "Section Plane"
        names = {
            section.name for section in self.sections
            if section is not current
        }

        if base not in names:
            return base

        index = 1

        while f"{base} {index}" in names:
            index += 1

        return f"{base} {index}"


def _vector_to_data(vector):

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def _vector_from_data(data):

    if data is None:
        return Vector3()

    return Vector3(data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))

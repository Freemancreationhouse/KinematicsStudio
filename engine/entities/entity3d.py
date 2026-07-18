from engine.geometry import BoundingBox3D, BoundingSphere, Matrix4, MeshData, Vector3


class Entity3D:
    """Base class for reusable 3D scene entities."""

    type_name = "Entity3D"
    is_3d = True

    def __init__(self, name=None):

        self.name = name or self.type_name
        self.visible = True
        self.locked = False
        self.selected = False
        self.hovered = False
        self.layer = None
        self.layer_id = None
        self.layer_name = None
        self.color = None
        self.position3d = Vector3()
        self.rotation3d = Vector3()
        self.scale3d = Vector3(1.0, 1.0, 1.0)
        self.transform = Matrix4.identity()

    # --------------------------------

    @property
    def bounding_box3d(self):
        """Return this entity's local 3D bounds."""

        return BoundingBox3D()

    # --------------------------------

    @property
    def bounding_sphere(self):
        """Return this entity's coarse bounding sphere."""

        return BoundingSphere.from_box(self.bounding_box3d)

    # --------------------------------

    @property
    def display_color(self):
        """Return the resolved display color."""

        return self.color or "#FFFFFF"

    # --------------------------------

    def points(self):
        """Return representative points for rendering and properties."""

        return []

    # --------------------------------

    def segments(self):
        """Return line segments for wire rendering."""

        return []

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe entity data."""

        return {
            "type": self.__class__.__name__,
            "name": self.name,
            "visible": self.visible,
            "locked": self.locked,
            "selected": self.selected,
            "layer_name": self.layer_name,
            "color": self.color,
            "position3d": _vector_to_data(self.position3d),
            "rotation3d": _vector_to_data(self.rotation3d),
            "scale3d": _vector_to_data(self.scale3d),
            "transform": list(self.transform.values),
        }

    # --------------------------------

    def set_transform_state(self, position=None, rotation=None, scale=None):
        """Update editable transform state and rebuild the matrix."""

        if position is not None:
            self.position3d = position.copy()

        if rotation is not None:
            self.rotation3d = rotation.copy()

        if scale is not None:
            self.scale3d = scale.copy()

        self.transform = Matrix4.compose(
            self.position3d,
            self.rotation3d,
            self.scale3d,
        )

    # --------------------------------

    def transform_state(self):
        """Return detached editable transform values."""

        return {
            "position3d": self.position3d.copy(),
            "rotation3d": self.rotation3d.copy(),
            "scale3d": self.scale3d.copy(),
            "transform": self.transform.copy(),
        }

    # --------------------------------

    def _box_from_points(self, points):

        box = BoundingBox3D()

        for point in points:
            box.add(point)

        return box


class Point3D(Entity3D):
    """Selectable 3D point entity."""

    type_name = "Point3D"

    def __init__(self, position=None, name=None):

        super().__init__(name or "Point3D")
        self.position = position or Vector3()

    # --------------------------------

    @property
    def bounding_box3d(self):

        box = BoundingBox3D()
        pad = 2.0
        box.add(self.position - Vector3(pad, pad, pad))
        box.add(self.position + Vector3(pad, pad, pad))
        return box

    # --------------------------------

    def points(self):

        return [self.position]

    # --------------------------------

    def to_dict(self):

        data = super().to_dict()
        data["position"] = _vector_to_data(self.position)
        return data


class Line3D(Entity3D):
    """Selectable 3D line segment."""

    type_name = "Line3D"

    def __init__(self, start=None, end=None, name=None):

        super().__init__(name or "Line3D")
        self.start = start or Vector3()
        self.end = end or Vector3(100.0, 0.0, 0.0)

    # --------------------------------

    @property
    def bounding_box3d(self):

        return self._box_from_points([self.start, self.end])

    # --------------------------------

    def points(self):

        return [self.start, self.end]

    # --------------------------------

    def segments(self):

        return [(self.start, self.end)]

    # --------------------------------

    def to_dict(self):

        data = super().to_dict()
        data["start"] = _vector_to_data(self.start)
        data["end"] = _vector_to_data(self.end)
        return data


class Polyline3D(Entity3D):
    """Selectable 3D polyline entity."""

    type_name = "Polyline3D"

    def __init__(self, points=None, closed=False, name=None):

        super().__init__(name or "Polyline3D")
        self._points = list(points or [])
        self.closed = bool(closed)

    # --------------------------------

    @property
    def bounding_box3d(self):

        return self._box_from_points(self._points)

    # --------------------------------

    def points(self):

        return list(self._points)

    # --------------------------------

    def segments(self):

        pairs = list(zip(self._points, self._points[1:]))

        if self.closed and len(self._points) > 2:
            pairs.append((self._points[-1], self._points[0]))

        return pairs

    # --------------------------------

    def to_dict(self):

        data = super().to_dict()
        data["points"] = [_vector_to_data(point) for point in self._points]
        data["closed"] = self.closed
        return data


class PlaneEntity(Entity3D):
    """Reference 3D plane represented by a rectangular wire boundary."""

    type_name = "PlaneEntity"

    def __init__(self, origin=None, width=200.0, height=200.0, name=None):

        super().__init__(name or "PlaneEntity")
        self.origin = origin or Vector3()
        self.width = float(width)
        self.height = float(height)

    # --------------------------------

    def points(self):

        half_width = self.width * 0.5
        half_height = self.height * 0.5

        return [
            self.origin + Vector3(-half_width, -half_height, 0.0),
            self.origin + Vector3(half_width, -half_height, 0.0),
            self.origin + Vector3(half_width, half_height, 0.0),
            self.origin + Vector3(-half_width, half_height, 0.0),
        ]

    # --------------------------------

    @property
    def bounding_box3d(self):

        return self._box_from_points(self.points())

    # --------------------------------

    def segments(self):

        pts = self.points()
        return list(zip(pts, pts[1:] + pts[:1]))

    # --------------------------------

    def to_dict(self):

        data = super().to_dict()
        data["origin"] = _vector_to_data(self.origin)
        data["width"] = self.width
        data["height"] = self.height
        return data


class ReferenceAxis(Line3D):
    """Named 3D reference axis."""

    type_name = "ReferenceAxis"

    def __init__(self, start=None, end=None, axis="X", name=None):

        super().__init__(start, end, name or f"{axis} Axis")
        self.axis = axis

    # --------------------------------

    def to_dict(self):

        data = super().to_dict()
        data["axis"] = self.axis
        return data


class ReferenceGrid(Entity3D):
    """Reference grid entity for scene graph organization."""

    type_name = "ReferenceGrid"

    def __init__(self, size=500.0, spacing=50.0, name=None):

        super().__init__(name or "ReferenceGrid")
        self.size = float(size)
        self.spacing = float(spacing)

    # --------------------------------

    @property
    def bounding_box3d(self):

        half = self.size * 0.5
        return self._box_from_points([
            Vector3(-half, -half, 0.0),
            Vector3(half, half, 0.0),
        ])

    # --------------------------------

    def segments(self):

        half = self.size * 0.5
        lines = []
        count = int(self.size / max(self.spacing, 1.0))

        for index in range(-count // 2, count // 2 + 1):
            value = index * self.spacing
            lines.append((Vector3(-half, value, 0.0), Vector3(half, value, 0.0)))
            lines.append((Vector3(value, -half, 0.0), Vector3(value, half, 0.0)))

        return lines

    # --------------------------------

    def to_dict(self):

        data = super().to_dict()
        data["size"] = self.size
        data["spacing"] = self.spacing
        return data


class MeshEntity(Entity3D):
    """Selectable static mesh entity for generated and imported 3D mesh data."""

    type_name = "MeshEntity"

    def __init__(
        self,
        mesh_data=None,
        name=None,
        display_mode="wireframe",
        primitive_type=None,
        parameters=None,
    ):

        super().__init__(name or "MeshEntity")
        self.mesh_data = mesh_data or MeshData()
        self.display_mode = display_mode
        self.show_bounds = False
        self.primitive_type = primitive_type
        self.parameters = dict(parameters or {})

    # --------------------------------

    @property
    def bounding_box3d(self):

        return self._box_from_points(self.points())

    # --------------------------------

    @property
    def bounding_sphere(self):

        return BoundingSphere.from_box(self.bounding_box3d)

    # --------------------------------

    def points(self):

        return [
            self.transform.transform_point(point)
            for point in self.mesh_data.positions()
        ]

    # --------------------------------

    def segments(self):

        return [
            (
                self.transform.transform_point(start),
                self.transform.transform_point(end),
            )
            for start, end in self.mesh_data.edge_segments()
        ]

    # --------------------------------

    def triangles(self):

        return [
            (
                self.transform.transform_point(a),
                self.transform.transform_point(b),
                self.transform.transform_point(c),
            )
            for a, b, c in self.mesh_data.face_triangles()
        ]

    # --------------------------------

    def to_dict(self):

        data = super().to_dict()
        data["mesh_data"] = self.mesh_data.to_dict()
        data["display_mode"] = self.display_mode
        data["show_bounds"] = self.show_bounds
        data["primitive_type"] = self.primitive_type
        data["parameters"] = dict(self.parameters)
        return data


def entity3d_from_dict(data):
    """Create a 3D entity from persisted data."""

    entity_type = data.get("type")

    if entity_type == "Point3D":
        entity = Point3D(_vector_from_data(data.get("position")), data.get("name"))
    elif entity_type == "Line3D":
        entity = Line3D(
            _vector_from_data(data.get("start")),
            _vector_from_data(data.get("end")),
            data.get("name"),
        )
    elif entity_type == "Polyline3D":
        entity = Polyline3D(
            [_vector_from_data(point) for point in data.get("points", [])],
            data.get("closed", False),
            data.get("name"),
        )
    elif entity_type == "PlaneEntity":
        entity = PlaneEntity(
            _vector_from_data(data.get("origin")),
            data.get("width", 200.0),
            data.get("height", 200.0),
            data.get("name"),
        )
    elif entity_type == "ReferenceAxis":
        entity = ReferenceAxis(
            _vector_from_data(data.get("start")),
            _vector_from_data(data.get("end")),
            data.get("axis", "X"),
            data.get("name"),
        )
    elif entity_type == "ReferenceGrid":
        entity = ReferenceGrid(
            data.get("size", 500.0),
            data.get("spacing", 50.0),
            data.get("name"),
        )
    elif entity_type == "MeshEntity":
        entity = MeshEntity(
            MeshData.from_dict(data.get("mesh_data", {})),
            data.get("name"),
            data.get("display_mode", "wireframe"),
            data.get("primitive_type"),
            data.get("parameters", {}),
        )
        entity.show_bounds = bool(data.get("show_bounds", False))
    else:
        entity = Entity3D(data.get("name"))

    entity.visible = bool(data.get("visible", True))
    entity.locked = bool(data.get("locked", False))
    entity.selected = bool(data.get("selected", False))
    entity.layer_name = data.get("layer_name")
    entity.color = data.get("color")
    transform = data.get("transform")

    if transform:
        entity.transform = Matrix4(transform)

    entity.position3d = _vector_from_data(data.get("position3d"))
    entity.rotation3d = _vector_from_data(data.get("rotation3d"))
    entity.scale3d = _vector_from_data(data.get("scale3d") or {"x": 1.0, "y": 1.0, "z": 1.0})

    return entity


def _vector_to_data(vector):

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def _vector_from_data(data):

    data = data or {}

    return Vector3(data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))

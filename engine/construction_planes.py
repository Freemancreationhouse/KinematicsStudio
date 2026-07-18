from engine.geometry import Vector3


class ConstructionPlane:
    """Reusable 3D construction plane definition."""

    def __init__(
        self,
        name,
        origin=None,
        normal=None,
        x_axis=None,
        y_axis=None,
        visible=True,
        locked=False,
    ):

        self.name = str(name)
        self.origin = origin or Vector3()
        self.normal = (normal or Vector3(0.0, 0.0, 1.0)).normalized()
        self.x_axis = (x_axis or Vector3(1.0, 0.0, 0.0)).normalized()
        self.y_axis = (y_axis or self.normal.cross(self.x_axis)).normalized()
        self.visible = bool(visible)
        self.locked = bool(locked)

    # --------------------------------

    @staticmethod
    def xy(name="XY Plane", offset=0.0):
        """Return an XY construction plane."""

        return ConstructionPlane(
            name,
            Vector3(0.0, 0.0, offset),
            Vector3(0.0, 0.0, 1.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        )

    # --------------------------------

    @staticmethod
    def yz(name="YZ Plane", offset=0.0):
        """Return a YZ construction plane."""

        return ConstructionPlane(
            name,
            Vector3(offset, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
            Vector3(0.0, 0.0, 1.0),
        )

    # --------------------------------

    @staticmethod
    def zx(name="ZX Plane", offset=0.0):
        """Return a ZX construction plane."""

        return ConstructionPlane(
            name,
            Vector3(0.0, offset, 0.0),
            Vector3(0.0, 1.0, 0.0),
            Vector3(0.0, 0.0, 1.0),
            Vector3(1.0, 0.0, 0.0),
        )

    # --------------------------------

    def offset(self, name, distance):
        """Return a new plane offset along this plane's normal."""

        return ConstructionPlane(
            name,
            self.origin + self.normal * float(distance),
            self.normal,
            self.x_axis,
            self.y_axis,
            self.visible,
            self.locked,
        )

    # --------------------------------

    def rotated(self, name, angle_degrees):
        """Return a plane rotated around its normal."""

        from engine.geometry import Matrix4

        matrix = Matrix4.rotation_euler(self.normal * float(angle_degrees))
        x_axis = matrix.transform_point(self.x_axis)
        y_axis = matrix.transform_point(self.y_axis)

        return ConstructionPlane(
            name,
            self.origin,
            self.normal,
            x_axis,
            y_axis,
            self.visible,
            self.locked,
        )

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe plane data."""

        return {
            "name": self.name,
            "origin": _vector_to_data(self.origin),
            "normal": _vector_to_data(self.normal),
            "x_axis": _vector_to_data(self.x_axis),
            "y_axis": _vector_to_data(self.y_axis),
            "visible": self.visible,
            "locked": self.locked,
        }

    # --------------------------------

    @staticmethod
    def from_dict(data):
        """Create a construction plane from persisted data."""

        data = data or {}

        return ConstructionPlane(
            data.get("name", "Construction Plane"),
            _vector_from_data(data.get("origin")),
            _vector_from_data(data.get("normal") or {"z": 1.0}),
            _vector_from_data(data.get("x_axis") or {"x": 1.0}),
            _vector_from_data(data.get("y_axis") or {"y": 1.0}),
            data.get("visible", True),
            data.get("locked", False),
        )


class ConstructionPlaneManager:
    """Workspace-owned construction plane manager."""

    def __init__(self):

        self.planes = []
        self.active = None
        self._create_defaults()

    # --------------------------------

    def create(self, name, origin=None, normal=None, x_axis=None, y_axis=None):
        """Create a unique custom construction plane."""

        plane = ConstructionPlane(
            self._unique_name(name),
            origin,
            normal,
            x_axis,
            y_axis,
        )
        self.planes.append(plane)

        return plane

    # --------------------------------

    def create_offset(self, source, name, distance):
        """Create a plane offset from an existing plane."""

        source = self.get(source) or self.active
        plane = source.offset(self._unique_name(name), distance)
        self.planes.append(plane)

        return plane

    # --------------------------------

    def create_rotated(self, source, name, angle_degrees):
        """Create a plane rotated from an existing plane."""

        source = self.get(source) or self.active
        plane = source.rotated(self._unique_name(name), angle_degrees)
        self.planes.append(plane)

        return plane

    # --------------------------------

    def set_active(self, plane):
        """Set active construction plane by object or name."""

        target = self.get(plane)

        if target is not None:
            self.active = target

        return self.active

    # --------------------------------

    def get(self, plane):
        """Return a construction plane by object or name."""

        if isinstance(plane, ConstructionPlane):
            return plane if plane in self.planes else None

        for item in self.planes:
            if item.name == plane:
                return item

        return None

    # --------------------------------

    def names(self):
        """Return plane names."""

        return [plane.name for plane in self.planes]

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe manager data."""

        return {
            "active": getattr(self.active, "name", "XY Plane"),
            "planes": [plane.to_dict() for plane in self.planes],
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore planes from persisted data."""

        data = data or {}
        items = data.get("planes", [])

        if items:
            self.planes = [ConstructionPlane.from_dict(item) for item in items]

        self.active = self.get(data.get("active")) or (self.planes[0] if self.planes else None)

    # --------------------------------

    def _create_defaults(self):

        self.planes = [
            ConstructionPlane.xy(),
            ConstructionPlane.yz(),
            ConstructionPlane.zx(),
        ]
        self.active = self.planes[0]

    # --------------------------------

    def _unique_name(self, name):

        base = str(name or "Construction Plane").strip() or "Construction Plane"
        names = set(self.names())

        if base not in names:
            return base

        index = 1

        while f"{base} {index}" in names:
            index += 1

        return f"{base} {index}"


def _vector_to_data(vector):

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def _vector_from_data(data):

    data = data or {}

    return Vector3(data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))

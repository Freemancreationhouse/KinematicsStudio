from engine.geometry import Vector3


class CoordinateSystem:
    """Reusable coordinate system with origin and orthonormal axes."""

    def __init__(self, name, origin=None, x_axis=None, y_axis=None, z_axis=None, system_type="UCS"):

        self.name = str(name)
        self.origin = origin or Vector3()
        self.x_axis = (x_axis or Vector3(1.0, 0.0, 0.0)).normalized()
        self.y_axis = (y_axis or Vector3(0.0, 1.0, 0.0)).normalized()
        self.z_axis = (z_axis or self.x_axis.cross(self.y_axis)).normalized()
        self.system_type = system_type
        self.visible = True
        self.locked = False

    # --------------------------------

    def to_world(self, point):
        """Convert a local point to world coordinates."""

        return (
            self.origin +
            self.x_axis * point.x +
            self.y_axis * point.y +
            self.z_axis * point.z
        )

    # --------------------------------

    def from_world(self, point):
        """Convert a world point to local coordinates."""

        offset = point - self.origin

        return Vector3(
            offset.dot(self.x_axis),
            offset.dot(self.y_axis),
            offset.dot(self.z_axis),
        )

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe coordinate system data."""

        return {
            "name": self.name,
            "origin": _vector_to_data(self.origin),
            "x_axis": _vector_to_data(self.x_axis),
            "y_axis": _vector_to_data(self.y_axis),
            "z_axis": _vector_to_data(self.z_axis),
            "system_type": self.system_type,
            "visible": self.visible,
            "locked": self.locked,
        }

    # --------------------------------

    @staticmethod
    def from_dict(data):
        """Create a coordinate system from persisted data."""

        data = data or {}
        system = CoordinateSystem(
            data.get("name", "UCS"),
            _vector_from_data(data.get("origin")),
            _vector_from_data(data.get("x_axis") or {"x": 1.0}),
            _vector_from_data(data.get("y_axis") or {"y": 1.0}),
            _vector_from_data(data.get("z_axis") or {"z": 1.0}),
            data.get("system_type", "UCS"),
        )
        system.visible = bool(data.get("visible", True))
        system.locked = bool(data.get("locked", False))

        return system


class CoordinateSystemManager:
    """Workspace-owned WCS/UCS/LCS manager with grid settings."""

    def __init__(self):

        self.systems = []
        self.active = None
        self.grid_spacing = 50.0
        self.grid_subdivisions = 5
        self.grid_visible = True
        self._create_defaults()

    # --------------------------------

    @property
    def wcs(self):
        """Return the World Coordinate System."""

        return self.get("WCS")

    # --------------------------------

    def create_ucs(self, name, origin=None, x_axis=None, y_axis=None, z_axis=None):
        """Create a unique user coordinate system."""

        system = CoordinateSystem(
            self._unique_name(name),
            origin,
            x_axis,
            y_axis,
            z_axis,
            "UCS",
        )
        self.systems.append(system)

        return system

    # --------------------------------

    def create_lcs(self, name, entity):
        """Create a local coordinate system from a 3D entity."""

        origin = getattr(entity, "position3d", Vector3())
        system = CoordinateSystem(self._unique_name(name), origin, system_type="LCS")
        self.systems.append(system)

        return system

    # --------------------------------

    def rename(self, system, new_name):
        """Rename a non-WCS coordinate system."""

        target = self.get(system)

        if target is None or target.system_type == "WCS":
            return False

        target.name = self._unique_name(new_name)

        return True

    # --------------------------------

    def delete(self, system):
        """Delete a non-WCS coordinate system."""

        target = self.get(system)

        if target is None or target.system_type == "WCS":
            return False

        self.systems.remove(target)

        if self.active is target:
            self.active = self.wcs

        return True

    # --------------------------------

    def activate(self, system):
        """Activate a coordinate system by object or name."""

        target = self.get(system)

        if target is not None:
            self.active = target

        return self.active

    # --------------------------------

    def get(self, system):
        """Return a coordinate system by object or name."""

        if isinstance(system, CoordinateSystem):
            return system if system in self.systems else None

        for item in self.systems:
            if item.name == system:
                return item

        return None

    # --------------------------------

    def names(self):
        """Return coordinate system names."""

        return [system.name for system in self.systems]

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe manager data."""

        return {
            "active": getattr(self.active, "name", "WCS"),
            "grid_spacing": self.grid_spacing,
            "grid_subdivisions": self.grid_subdivisions,
            "grid_visible": self.grid_visible,
            "systems": [system.to_dict() for system in self.systems],
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore coordinate systems and grid settings."""

        data = data or {}
        items = data.get("systems", [])

        if items:
            self.systems = [CoordinateSystem.from_dict(item) for item in items]

        self.grid_spacing = float(data.get("grid_spacing", self.grid_spacing))
        self.grid_subdivisions = int(data.get("grid_subdivisions", self.grid_subdivisions))
        self.grid_visible = bool(data.get("grid_visible", self.grid_visible))
        self.active = self.get(data.get("active")) or self.wcs

    # --------------------------------

    def _create_defaults(self):

        self.systems = [
            CoordinateSystem("WCS", system_type="WCS"),
        ]
        self.active = self.systems[0]

    # --------------------------------

    def _unique_name(self, name):

        base = str(name or "UCS").strip() or "UCS"
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

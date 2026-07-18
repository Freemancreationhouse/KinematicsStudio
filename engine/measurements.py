import math
from dataclasses import dataclass

from engine.geometry import BoundingBox3D, Vector3


@dataclass
class MeasurementResult:
    """Computed measurement value with display metadata."""

    measurement_type: str
    value: object
    units: str = ""
    label: str = ""


class MeasurementSettings:
    """Display and precision settings for 3D measurements."""

    def __init__(self):

        self.visible = True
        self.precision = 3
        self.show_labels = True
        self.show_markers = True
        self.color = "#ffcc66"

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe settings data."""

        return {
            "visible": self.visible,
            "precision": self.precision,
            "show_labels": self.show_labels,
            "show_markers": self.show_markers,
            "color": self.color,
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore settings from persisted data."""

        data = data or {}
        self.visible = bool(data.get("visible", self.visible))
        self.precision = int(data.get("precision", self.precision))
        self.show_labels = bool(data.get("show_labels", self.show_labels))
        self.show_markers = bool(data.get("show_markers", self.show_markers))
        self.color = data.get("color", self.color)


class Measurement:
    """Persistent selectable 3D measurement entity."""

    type_name = "Measurement"
    is_3d = True
    is_measurement = True

    def __init__(self, measurement_type, points=None, result=None, name=None):

        self.name = name or measurement_type
        self.measurement_type = measurement_type
        self.points = [point.copy() for point in (points or [])]
        self.result = result or MeasurementResult(measurement_type, 0.0)
        self.visible = True
        self.locked = False
        self.selected = False
        self.hovered = False
        self.layer = None
        self.layer_id = None
        self.layer_name = None
        self.color = "#ffcc66"

    # --------------------------------

    @property
    def bounding_box3d(self):
        """Return measurement bounds."""

        box = BoundingBox3D()

        for point in self.points:
            box.add(point)

        return box

    # --------------------------------

    @property
    def display_color(self):
        """Return measurement display color."""

        return self.color or "#ffcc66"

    # --------------------------------

    def segments(self):
        """Return measurement line graphics."""

        if len(self.points) < 2:
            return []

        return list(zip(self.points, self.points[1:]))

    # --------------------------------

    def representative_points(self):
        """Return marker points for rendering."""

        return list(self.points)

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe measurement data."""

        return {
            "name": self.name,
            "measurement_type": self.measurement_type,
            "points": [_vector_to_data(point) for point in self.points],
            "result": {
                "measurement_type": self.result.measurement_type,
                "value": self.result.value,
                "units": self.result.units,
                "label": self.result.label,
            },
            "visible": self.visible,
            "locked": self.locked,
            "selected": self.selected,
            "layer_name": self.layer_name,
            "color": self.color,
        }

    # --------------------------------

    @staticmethod
    def from_dict(data):
        """Restore a measurement from persisted data."""

        data = data or {}
        result_data = data.get("result", {})
        measurement = Measurement(
            data.get("measurement_type", "Measurement"),
            [_vector_from_data(point) for point in data.get("points", [])],
            MeasurementResult(
                result_data.get("measurement_type", data.get("measurement_type", "Measurement")),
                result_data.get("value", 0.0),
                result_data.get("units", ""),
                result_data.get("label", ""),
            ),
            data.get("name"),
        )
        measurement.visible = bool(data.get("visible", True))
        measurement.locked = bool(data.get("locked", False))
        measurement.selected = bool(data.get("selected", False))
        measurement.layer_name = data.get("layer_name")
        measurement.color = data.get("color", measurement.color)

        return measurement


class MeasurementManager:
    """Workspace-owned 3D measurement and inspection manager."""

    def __init__(self):

        self.measurements = []
        self.settings = MeasurementSettings()
        self.inspection_settings = {
            "show_normals": True,
            "show_centers": True,
            "show_bounding_boxes": True,
        }

    # --------------------------------

    def add(self, measurement):
        """Store a persistent measurement."""

        if measurement not in self.measurements:
            self.measurements.append(measurement)

        return measurement

    # --------------------------------

    def remove(self, measurement):
        """Remove a persistent measurement."""

        if measurement in self.measurements:
            self.measurements.remove(measurement)
            return True

        return False

    # --------------------------------

    def point_to_point(self, start, end, name=None):
        """Create a point-to-point distance measurement."""

        distance = start.distance_to(end)

        return Measurement(
            "Point-to-Point Distance",
            [start, end],
            MeasurementResult("Point-to-Point Distance", distance, "units", _label(distance)),
            name,
        )

    # --------------------------------

    def edge_length(self, start, end, name=None):
        """Create an edge length measurement."""

        return self.point_to_point(start, end, name or "Edge Length")

    # --------------------------------

    def polyline_length(self, points, name=None):
        """Create a polyline length measurement."""

        value = sum(
            start.distance_to(end)
            for start, end in zip(points, points[1:])
        )

        return Measurement(
            "Polyline Length",
            list(points),
            MeasurementResult("Polyline Length", value, "units", _label(value)),
            name,
        )

    # --------------------------------

    def surface_area(self, triangle, name=None):
        """Create a single triangular surface area measurement."""

        value = _triangle_area(*triangle)

        return Measurement(
            "Surface Area",
            list(triangle),
            MeasurementResult("Surface Area", value, "sq units", _label(value)),
            name,
        )

    # --------------------------------

    def mesh_area(self, mesh_entity, name=None):
        """Create a mesh area measurement."""

        value = sum(_triangle_area(*triangle) for triangle in mesh_entity.triangles())
        box = mesh_entity.bounding_box3d

        return Measurement(
            "Mesh Area",
            box.corners()[:2],
            MeasurementResult("Mesh Area", value, "sq units", _label(value)),
            name,
        )

    # --------------------------------

    def bounding_box_size(self, entity, name=None):
        """Create a bounding-box size measurement."""

        box = entity.bounding_box3d
        size = box.size

        return Measurement(
            "Bounding Box Size",
            box.corners(),
            MeasurementResult(
                "Bounding Box Size",
                {"x": size.x, "y": size.y, "z": size.z},
                "units",
                f"{_label(size.x)} x {_label(size.y)} x {_label(size.z)}",
            ),
            name,
        )

    # --------------------------------

    def radius(self, center, point, name=None):
        """Create a radius measurement."""

        value = center.distance_to(point)

        return Measurement(
            "Radius",
            [center, point],
            MeasurementResult("Radius", value, "units", _label(value)),
            name,
        )

    # --------------------------------

    def diameter(self, center, point, name=None):
        """Create a diameter measurement."""

        value = center.distance_to(point) * 2.0

        return Measurement(
            "Diameter",
            [center, point],
            MeasurementResult("Diameter", value, "units", _label(value)),
            name,
        )

    # --------------------------------

    def angle(self, vertex, point1, point2, name=None):
        """Create an angle measurement."""

        a = (point1 - vertex).normalized()
        b = (point2 - vertex).normalized()
        value = math.degrees(math.acos(max(-1.0, min(1.0, a.dot(b)))))

        return Measurement(
            "Angle",
            [point1, vertex, point2],
            MeasurementResult("Angle", value, "deg", _label(value)),
            name,
        )

    # --------------------------------

    def coordinate_readout(self, point, coordinate_system=None, name=None):
        """Create a coordinate readout measurement."""

        local = coordinate_system.from_world(point) if coordinate_system else point

        return Measurement(
            "Coordinate Readout",
            [point],
            MeasurementResult(
                "Coordinate Readout",
                {"x": local.x, "y": local.y, "z": local.z},
                "units",
                f"X {_label(local.x)} Y {_label(local.y)} Z {_label(local.z)}",
            ),
            name,
        )

    # --------------------------------

    def xyz_delta(self, start, end, name=None):
        """Create an XYZ delta measurement."""

        delta = end - start

        return Measurement(
            "XYZ Delta",
            [start, end],
            MeasurementResult(
                "XYZ Delta",
                {"x": delta.x, "y": delta.y, "z": delta.z},
                "units",
                f"dX {_label(delta.x)} dY {_label(delta.y)} dZ {_label(delta.z)}",
            ),
            name,
        )

    # --------------------------------

    def minimum_distance(self, first, second, name=None):
        """Create a minimum distance measurement between representative points."""

        start, end, value = _extreme_distance(first.points(), second.points(), minimum=True)

        return Measurement(
            "Minimum Distance",
            [start, end],
            MeasurementResult("Minimum Distance", value, "units", _label(value)),
            name,
        )

    # --------------------------------

    def maximum_distance(self, first, second, name=None):
        """Create a maximum distance measurement between representative points."""

        start, end, value = _extreme_distance(first.points(), second.points(), minimum=False)

        return Measurement(
            "Maximum Distance",
            [start, end],
            MeasurementResult("Maximum Distance", value, "units", _label(value)),
            name,
        )

    # --------------------------------

    def inspect_point(self, point):
        """Return point inspection data."""

        return {"type": "Point Inspection", "point": point}

    # --------------------------------

    def inspect_edge(self, start, end):
        """Return edge inspection data."""

        return {
            "type": "Edge Inspection",
            "start": start,
            "end": end,
            "length": start.distance_to(end),
        }

    # --------------------------------

    def inspect_face(self, triangle):
        """Return face inspection data."""

        normal = (triangle[1] - triangle[0]).cross(triangle[2] - triangle[0]).normalized()

        return {
            "type": "Face Inspection",
            "area": _triangle_area(*triangle),
            "normal": normal,
            "center": (triangle[0] + triangle[1] + triangle[2]) / 3.0,
        }

    # --------------------------------

    def mesh_statistics(self, mesh_entity):
        """Return mesh statistics."""

        mesh = mesh_entity.mesh_data

        return {
            "type": "Mesh Statistics",
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "faces": len(mesh.faces),
            "triangles": len(mesh.triangle_indices),
            "area": sum(_triangle_area(*triangle) for triangle in mesh_entity.triangles()),
            "volume": None,
        }

    # --------------------------------

    def bounding_box_inspection(self, entity):
        """Return bounding box inspection data."""

        box = entity.bounding_box3d

        return {
            "type": "Bounding Box Inspection",
            "min": box.min,
            "max": box.max,
            "size": box.size,
            "center": box.center,
        }

    # --------------------------------

    def center_of_mass(self, entity):
        """Return a foundation center-of-mass approximation."""

        return getattr(entity, "bounding_box3d", BoundingBox3D()).center

    # --------------------------------

    def volume_placeholder(self, entity):
        """Return future-ready volume placeholder data."""

        return {
            "type": "Volume",
            "value": None,
            "status": "Future solid/closed-mesh volume support",
        }

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe measurement manager data."""

        return {
            "settings": self.settings.to_dict(),
            "inspection_settings": dict(self.inspection_settings),
            "measurements": [
                measurement.to_dict()
                for measurement in self.measurements
            ],
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore measurement manager data."""

        data = data or {}
        self.settings.from_dict(data.get("settings", {}))
        self.inspection_settings.update(data.get("inspection_settings", {}))
        self.measurements = [
            Measurement.from_dict(item)
            for item in data.get("measurements", [])
        ]


def _triangle_area(a, b, c):

    return (b - a).cross(c - a).length() * 0.5


def _extreme_distance(first_points, second_points, minimum=True):

    best = None

    for start in first_points:
        for end in second_points:
            value = start.distance_to(end)

            if best is None:
                best = (start, end, value)
            elif minimum and value < best[2]:
                best = (start, end, value)
            elif not minimum and value > best[2]:
                best = (start, end, value)

    return best or (Vector3(), Vector3(), 0.0)


def _label(value):

    return f"{value:.3f}"


def _vector_to_data(vector):

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def _vector_from_data(data):

    data = data or {}

    return Vector3(data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))

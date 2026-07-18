from engine.geometry import BoundingBox3D, Vector3


class TransformGizmo:
    """Reusable transform gizmo state for 3D command integration."""

    MODES = ("translate", "rotate", "scale")
    AXES = ("X", "Y", "Z")
    PLANES = ("XY", "XZ", "YZ")
    COORDINATE_MODES = ("world", "local")
    PIVOT_MODES = ("center", "origin", "individual", "bounding_box_center")

    def __init__(self):

        self.visible = True
        self.mode = "translate"
        self.highlighted_axis = None
        self.axis_constraint = None
        self.plane_constraint = None
        self.coordinate_mode = "world"
        self.pivot_mode = "center"
        self.pivot = Vector3()
        self.size = 120.0
        self.debug_bounds = False

    # --------------------------------

    def set_mode(self, mode):
        """Switch gizmo mode without performing an edit."""

        if mode in self.MODES:
            self.mode = mode

    # --------------------------------

    def set_axis_constraint(self, axis):
        """Set or clear an axis transform constraint."""

        self.axis_constraint = axis if axis in self.AXES else None

        if self.axis_constraint:
            self.plane_constraint = None

    # --------------------------------

    def set_plane_constraint(self, plane):
        """Set or clear a plane transform constraint."""

        self.plane_constraint = plane if plane in self.PLANES else None

        if self.plane_constraint:
            self.axis_constraint = None

    # --------------------------------

    def set_coordinate_mode(self, mode):
        """Switch between world and local transform orientation."""

        if mode in self.COORDINATE_MODES:
            self.coordinate_mode = mode

    # --------------------------------

    def set_pivot_mode(self, mode):
        """Switch the active pivot calculation mode."""

        if mode in self.PIVOT_MODES:
            self.pivot_mode = mode

    # --------------------------------

    def set_pivot(self, pivot):
        """Set an explicit pivot point."""

        self.pivot = pivot.copy()

    # --------------------------------

    def origin_for_selection(self, selection):
        """Return gizmo origin for the current selected 3D entities."""

        return self.pivot_for_selection(selection)

    # --------------------------------

    def pivot_for_selection(self, selection):
        """Return the active pivot for the selected 3D entities."""

        selected = [
            entity for entity in selection
            if getattr(entity, "is_3d", False)
        ]

        if self.pivot_mode == "origin":
            return Vector3()

        if self.pivot_mode == "individual" and selected:
            return getattr(selected[0], "position3d", Vector3()).copy()

        if self.pivot_mode == "center":
            return self._average_center(selected)

        boxes = [
            getattr(entity, "bounding_box3d", None)
            for entity in selected
        ]
        bounds = BoundingBox3D()

        for box in boxes:
            if box is None or not box.valid:
                continue

            for corner in box.corners():
                bounds.add(corner)

        if bounds.valid:
            return bounds.center

        return self.pivot.copy()

    # --------------------------------

    def axis_segments(self, origin):
        """Return axis segments for rendering."""

        scale = 0.75 if self.mode == "scale" else 1.0
        size = self.size * scale

        return {
            "X": (origin, origin + Vector3(size, 0.0, 0.0)),
            "Y": (origin, origin + Vector3(0.0, size, 0.0)),
            "Z": (origin, origin + Vector3(0.0, 0.0, size)),
        }

    # --------------------------------

    def pick_axis(self, ray, origin, tolerance=10.0):
        """Return the nearest picked axis name, or None."""

        best_axis = None
        best_distance = float("inf")

        for axis, (start, end) in self.axis_segments(origin).items():
            distance = _ray_segment_distance(ray, start, end)

            if distance < tolerance and distance < best_distance:
                best_axis = axis
                best_distance = distance

        self.highlighted_axis = best_axis

        return best_axis

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe gizmo state."""

        return {
            "visible": self.visible,
            "mode": self.mode,
            "highlighted_axis": self.highlighted_axis,
            "axis_constraint": self.axis_constraint,
            "plane_constraint": self.plane_constraint,
            "coordinate_mode": self.coordinate_mode,
            "pivot_mode": self.pivot_mode,
            "pivot": _vector_to_data(self.pivot),
            "size": self.size,
            "debug_bounds": self.debug_bounds,
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore gizmo state from persisted data."""

        data = data or {}
        self.visible = bool(data.get("visible", self.visible))
        self.set_mode(data.get("mode", self.mode))
        self.highlighted_axis = data.get("highlighted_axis")
        self.set_axis_constraint(data.get("axis_constraint"))
        self.set_plane_constraint(data.get("plane_constraint"))
        self.set_coordinate_mode(data.get("coordinate_mode", self.coordinate_mode))
        self.set_pivot_mode(data.get("pivot_mode", self.pivot_mode))
        self.pivot = _vector_from_data(data.get("pivot"))
        self.size = float(data.get("size", self.size))
        self.debug_bounds = bool(data.get("debug_bounds", self.debug_bounds))

    # --------------------------------

    def _average_center(self, selection):

        points = [
            getattr(entity, "bounding_box3d", BoundingBox3D()).center
            for entity in selection
            if getattr(entity, "bounding_box3d", BoundingBox3D()).valid
        ]

        if not points:
            return self.pivot.copy()

        total = Vector3()

        for point in points:
            total = total + point

        return total / len(points)


def _ray_segment_distance(ray, start, end):

    direction = ray.direction
    segment = end - start
    between = ray.origin - start
    a = direction.dot(direction)
    b = direction.dot(segment)
    c = segment.dot(segment)
    d = direction.dot(between)
    e = segment.dot(between)
    denominator = a * c - b * b

    if abs(denominator) < 1e-9:
        ray_t = 0.0
    else:
        ray_t = max(0.0, (b * e - c * d) / denominator)

    segment_t = 0.0 if c == 0.0 else max(0.0, min(1.0, (a * e - b * d) / denominator if abs(denominator) >= 1e-9 else 0.0))
    ray_point = ray.point_at(ray_t)
    segment_point = start + segment * segment_t

    return ray_point.distance_to(segment_point)


def _vector_to_data(vector):

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def _vector_from_data(data):

    data = data or {}

    return Vector3(data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))

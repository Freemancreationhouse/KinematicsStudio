import math
from dataclasses import dataclass, field
from uuid import uuid4


def _timestamp():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _f(value, default=0.0):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass
class SiteEngineeringSettings:
    """Reusable civil site engineering settings."""

    station_interval: float = 1.0
    slope_classes: list = field(default_factory=lambda: [0.0, 2.0, 5.0, 10.0, 20.0, 33.0])
    earthwork_grid_tolerance: float = 1e-6
    material_shrinkage: float = 0.0
    material_swell: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "station_interval": self.station_interval,
            "slope_classes": list(self.slope_classes),
            "earthwork_grid_tolerance": self.earthwork_grid_tolerance,
            "material_shrinkage": self.material_shrinkage,
            "material_swell": self.material_swell,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return SiteEngineeringSettings(
            _f(data.get("station_interval"), 1.0),
            list(data.get("slope_classes", [0.0, 2.0, 5.0, 10.0, 20.0, 33.0])),
            _f(data.get("earthwork_grid_tolerance"), 1e-6),
            _f(data.get("material_shrinkage"), 0.0),
            _f(data.get("material_swell"), 0.0),
            dict(data.get("metadata", {})),
        )


@dataclass
class SiteValidationReport:
    """Site engineering validation result."""

    valid: bool = True
    issues: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    statistics: dict = field(default_factory=dict)
    generated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        return {
            "valid": self.valid,
            "issues": list(self.issues),
            "warnings": list(self.warnings),
            "statistics": dict(self.statistics),
            "generated_at": self.generated_at,
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return SiteValidationReport(
            bool(data.get("valid", True)),
            list(data.get("issues", [])),
            list(data.get("warnings", [])),
            dict(data.get("statistics", {})),
            data.get("generated_at", _timestamp()),
        )


@dataclass
class SiteDiagnostics:
    """Site engineering diagnostics summary."""

    projects: int = 0
    grading_operations: int = 0
    volume_reports: int = 0
    slope_reports: int = 0
    drainage_reports: int = 0
    sections: int = 0
    profiles: int = 0
    boundaries: int = 0
    validation_issues: int = 0
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        data = data or {}
        return SiteDiagnostics(
            int(data.get("projects", 0)),
            int(data.get("grading_operations", 0)),
            int(data.get("volume_reports", 0)),
            int(data.get("slope_reports", 0)),
            int(data.get("drainage_reports", 0)),
            int(data.get("sections", 0)),
            int(data.get("profiles", 0)),
            int(data.get("boundaries", 0)),
            int(data.get("validation_issues", 0)),
            data.get("updated_at", _timestamp()),
        )


@dataclass
class SiteProject:
    """Civil site engineering project metadata scoped to a terrain project."""

    name: str = "Site Engineering Project"
    settings: SiteEngineeringSettings = field(default_factory=SiteEngineeringSettings)
    metadata: dict = field(default_factory=dict)
    grading_operations: list = field(default_factory=list)
    volume_reports: list = field(default_factory=list)
    slope_reports: list = field(default_factory=list)
    drainage_reports: list = field(default_factory=list)
    sections: list = field(default_factory=list)
    profiles: list = field(default_factory=list)
    boundaries: list = field(default_factory=list)
    visualization_metadata: dict = field(default_factory=dict)
    validation_report: SiteValidationReport = field(default_factory=SiteValidationReport)
    diagnostics: SiteDiagnostics = field(default_factory=SiteDiagnostics)
    id: str = field(default_factory=lambda: str(uuid4()))
    version_metadata: dict = field(default_factory=lambda: {"release": "2.0", "batch": "C"})

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "settings": self.settings.to_dict(),
            "metadata": dict(self.metadata),
            "grading_operations": [dict(item) for item in self.grading_operations],
            "volume_reports": [dict(item) for item in self.volume_reports],
            "slope_reports": [dict(item) for item in self.slope_reports],
            "drainage_reports": [dict(item) for item in self.drainage_reports],
            "sections": [dict(item) for item in self.sections],
            "profiles": [dict(item) for item in self.profiles],
            "boundaries": [dict(item) for item in self.boundaries],
            "visualization_metadata": dict(self.visualization_metadata),
            "validation_report": self.validation_report.to_dict(),
            "diagnostics": self.diagnostics.to_dict(),
            "version_metadata": dict(self.version_metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        project = SiteProject(
            data.get("name", "Site Engineering Project"),
            SiteEngineeringSettings.from_dict(data.get("settings", {})),
            dict(data.get("metadata", {})),
            [dict(item) for item in data.get("grading_operations", [])],
            [dict(item) for item in data.get("volume_reports", [])],
            [dict(item) for item in data.get("slope_reports", [])],
            [dict(item) for item in data.get("drainage_reports", [])],
            [dict(item) for item in data.get("sections", [])],
            [dict(item) for item in data.get("profiles", [])],
            [dict(item) for item in data.get("boundaries", [])],
            dict(data.get("visualization_metadata", {})),
            SiteValidationReport.from_dict(data.get("validation_report", {})),
            SiteDiagnostics.from_dict(data.get("diagnostics", {})),
            data.get("id", str(uuid4())),
            dict(data.get("version_metadata", {"release": "2.0", "batch": "C"})),
        )
        return project


class SiteEngineeringManager:
    """Terrain-scoped civil engineering manager; owns metadata and analysis only."""

    def __init__(self, terrain_manager=None):
        self.terrain_manager = terrain_manager
        self.projects = []
        self.active_project_id = None
        from engine.infrastructure import InfrastructureManager
        self.infrastructure_manager = InfrastructureManager(self)
        self.infrastructure = self.infrastructure_manager

    @property
    def active_project(self):
        if not self.projects:
            return None
        return self.get_project(self.active_project_id) or self.projects[-1]

    def create_project(self, name="Site Engineering Project", settings=None, metadata=None):
        project = SiteProject(name, settings if isinstance(settings, SiteEngineeringSettings) else SiteEngineeringSettings.from_dict(settings or {}), dict(metadata or {}))
        self.projects.append(project)
        self.active_project_id = project.id
        self.refresh_diagnostics(project)
        return project

    def ensure_project(self):
        return self.active_project or self.create_project()

    def get_project(self, project):
        if isinstance(project, SiteProject):
            return project if project in self.projects else None
        return next((item for item in self.projects if item.id == project or item.name == project), None)

    def terrain_surface(self, surface):
        if self.terrain_manager is None:
            raise ValueError("Site Engineering requires the existing Terrain Manager.")
        target = self.terrain_manager.surface_for(surface)
        if target is None:
            raise ValueError("Terrain surface not found for site engineering.")
        return target

    def add_boundary(self, name, boundary_type, polygon, metadata=None):
        if len(polygon or []) < 3:
            raise ValueError("Site boundary requires at least three polygon points.")
        record = {
            "id": str(uuid4()),
            "name": name,
            "boundary_type": boundary_type,
            "polygon": [list(map(float, point[:2])) for point in polygon],
            "area": _polygon_area(polygon),
            "metadata": dict(metadata or {}),
            "created_at": _timestamp(),
        }
        self.ensure_project().boundaries.append(record)
        self.refresh_diagnostics()
        return record

    def apply_grading(self, surface, grading_type, region, parameters=None):
        target = self.terrain_surface(surface)
        parameters = dict(parameters or {})
        before = [list(point) for point in target.points]
        affected = []
        for idx, point in enumerate(target.points):
            if not _point_in_region(point, region):
                continue
            old_z = point[2]
            point[2] = _graded_elevation(point, old_z, grading_type, region or {}, parameters)
            if abs(point[2] - old_z) > 1e-9:
                affected.append(idx)
        if not affected:
            raise ValueError("Grading region does not affect any terrain points.")
        target.metadata["last_site_grading"] = {"type": grading_type, "affected_points": len(affected), "timestamp": _timestamp()}
        if self.terrain_manager:
            self.terrain_manager.refresh_diagnostics()
        record = {
            "id": str(uuid4()),
            "surface_id": target.id,
            "surface_name": target.name,
            "grading_type": grading_type,
            "region": dict(region or {}),
            "parameters": parameters,
            "affected_points": list(affected),
            "before_points": before,
            "after_points": [list(point) for point in target.points],
            "created_at": _timestamp(),
            "validation": {"valid": True, "message": "Grading applied to terrain points."},
        }
        self.ensure_project().grading_operations.append(record)
        self.refresh_diagnostics()
        return record

    def compute_cut_fill(self, existing_surface, design_surface=None, region=None, name="Earthwork Volume"):
        existing = self.terrain_surface(existing_surface)
        design = self.terrain_surface(design_surface) if design_surface is not None else existing
        if design is existing:
            grading = self.ensure_project().grading_operations[-1] if self.ensure_project().grading_operations else None
            if not grading or grading.get("surface_id") != existing.id:
                raise ValueError("Cut/fill requires a design surface or a recorded grading operation for the selected surface.")
            baseline = grading["before_points"]
            proposed = grading["after_points"]
            triangles = existing.triangles
        else:
            baseline = existing.points
            proposed = _sample_design_on_existing(existing, design)
            triangles = existing.triangles
        cut, fill, region_area = _earthwork_volumes(baseline, proposed, triangles, region)
        shrinkage = self.ensure_project().settings.material_shrinkage
        swell = self.ensure_project().settings.material_swell
        report = {
            "id": str(uuid4()),
            "name": name,
            "existing_surface_id": existing.id,
            "design_surface_id": design.id,
            "region": dict(region or {}),
            "cut_volume": cut,
            "fill_volume": fill,
            "net_volume": fill - cut,
            "balanced_volume": fill * (1.0 + swell) - cut * (1.0 - shrinkage),
            "area": region_area,
            "statistics": {"triangles": len(triangles), "method": "signed_prismatic_triangle_integration"},
            "created_at": _timestamp(),
            "validation": {"valid": True},
        }
        self.ensure_project().volume_reports.append(report)
        self.refresh_diagnostics()
        return report

    def analyze_slope(self, surface, region=None, classes=None, name="Slope Analysis"):
        target = self.terrain_surface(surface)
        classes = list(classes or self.ensure_project().settings.slope_classes)
        slopes = []
        classified = {str(cls): 0 for cls in classes}
        for tri in target.triangles:
            pts = [target.points[i] for i in tri]
            cx = sum(p[0] for p in pts) / 3.0
            cy = sum(p[1] for p in pts) / 3.0
            if region and not _point_in_region([cx, cy, 0.0], region):
                continue
            slope = _triangle_slope_percent(pts)
            slopes.append(slope)
            bucket = max((cls for cls in classes if slope >= cls), default=classes[0] if classes else 0.0)
            classified[str(bucket)] = classified.get(str(bucket), 0) + 1
        if not slopes:
            raise ValueError("Slope analysis region contains no terrain triangles.")
        report = {
            "id": str(uuid4()),
            "name": name,
            "surface_id": target.id,
            "region": dict(region or {}),
            "minimum_slope": min(slopes),
            "maximum_slope": max(slopes),
            "average_slope": sum(slopes) / len(slopes),
            "slope_classes": classified,
            "color_classification_metadata": _slope_colors(classes),
            "triangles_evaluated": len(slopes),
            "created_at": _timestamp(),
            "validation": {"valid": True},
        }
        self.ensure_project().slope_reports.append(report)
        self.refresh_diagnostics()
        return report

    def analyze_drainage(self, surface, name="Drainage Analysis"):
        target = self.terrain_surface(surface)
        neighbors = _surface_neighbors(target.triangles, len(target.points))
        flow_to = {}
        for idx, point in enumerate(target.points):
            lower = [n for n in neighbors[idx] if target.points[n][2] < point[2]]
            flow_to[idx] = min(lower, key=lambda n: target.points[n][2]) if lower else None
        accumulation = {idx: 1 for idx in range(len(target.points))}
        for idx in sorted(range(len(target.points)), key=lambda i: target.points[i][2], reverse=True):
            downstream = flow_to[idx]
            if downstream is not None:
                accumulation[downstream] += accumulation[idx]
        low_points = [
            {"point_index": idx, "point": list(target.points[idx]), "accumulation": accumulation[idx]}
            for idx, downstream in flow_to.items()
            if downstream is None
        ]
        paths = [_drainage_path(idx, target.points, flow_to) for idx in range(len(target.points)) if accumulation[idx] > 1]
        catchments = _catchment_areas(target, flow_to)
        report = {
            "id": str(uuid4()),
            "name": name,
            "surface_id": target.id,
            "flow_direction": {str(k): v for k, v in flow_to.items()},
            "flow_accumulation": {str(k): v for k, v in accumulation.items()},
            "watershed_metadata": {"low_point_count": len(low_points), "catchments": catchments},
            "drainage_paths": paths,
            "low_points": low_points,
            "catchment_areas": catchments,
            "diagnostics": {"points": len(target.points), "edges": sum(len(v) for v in neighbors.values()) // 2},
            "created_at": _timestamp(),
            "validation": {"valid": True},
        }
        self.ensure_project().drainage_reports.append(report)
        self.refresh_diagnostics()
        return report

    def create_section(self, surface, name, line, interval=None, section_type="Cross Section"):
        target = self.terrain_surface(surface)
        samples = self._sample_line(target, line, interval)
        record = {
            "id": str(uuid4()),
            "name": name,
            "surface_id": target.id,
            "section_type": section_type,
            "line": [list(map(float, point[:2])) for point in line],
            "stationing": [{"station": sample["station"], "point": sample["point"]} for sample in samples],
            "samples": samples,
            "diagnostics": {"sample_count": len(samples)},
            "created_at": _timestamp(),
        }
        self.ensure_project().sections.append(record)
        self.refresh_diagnostics()
        return record

    def create_profile(self, surface, name, polyline, interval=None):
        target = self.terrain_surface(surface)
        samples = []
        station_offset = 0.0
        for start, end in zip(polyline, polyline[1:]):
            segment = self._sample_line(target, [start, end], interval)
            for sample in segment[:-1]:
                item = dict(sample)
                item["station"] += station_offset
                samples.append(item)
            station_offset += _distance2(start, end)
        last = polyline[-1]
        samples.append({"station": station_offset, "point": [float(last[0]), float(last[1]), self.terrain_manager.elevation_at(target, last[0], last[1])]})
        record = {
            "id": str(uuid4()),
            "name": name,
            "surface_id": target.id,
            "profile_type": "Longitudinal Profile",
            "polyline": [list(map(float, point[:2])) for point in polyline],
            "samples": samples,
            "stationing_metadata": {"interval": interval or self.ensure_project().settings.station_interval, "length": station_offset},
            "diagnostics": {"sample_count": len(samples)},
            "created_at": _timestamp(),
        }
        self.ensure_project().profiles.append(record)
        self.refresh_diagnostics()
        return record

    def validate_project(self):
        project = self.ensure_project()
        issues, warnings = [], []
        if self.terrain_manager is None or self.terrain_manager.active_project is None:
            issues.append("Site Engineering requires an active terrain project.")
        for boundary in project.boundaries:
            if boundary.get("area", 0.0) <= 0.0:
                issues.append(f"Boundary '{boundary.get('name')}' has zero area.")
        for report in project.volume_reports + project.slope_reports + project.drainage_reports:
            if not report.get("validation", {}).get("valid", False):
                issues.append(f"Invalid site engineering report '{report.get('name')}'.")
        if not project.grading_operations:
            warnings.append("No grading operations recorded yet.")
        project.validation_report = SiteValidationReport(not issues, issues, warnings, self.refresh_diagnostics(project).to_dict())
        return project.validation_report

    def visualization_metadata(self):
        project = self.ensure_project()
        project.visualization_metadata = {
            "grade_visualization": {item["id"]: {"surface_id": item["surface_id"], "type": item["grading_type"], "affected_points": len(item["affected_points"])} for item in project.grading_operations},
            "cut_fill_visualization": {item["id"]: {"cut_volume": item["cut_volume"], "fill_volume": item["fill_volume"], "net_volume": item["net_volume"]} for item in project.volume_reports},
            "slope_visualization": {item["id"]: {"minimum": item["minimum_slope"], "maximum": item["maximum_slope"], "classes": item["slope_classes"]} for item in project.slope_reports},
            "drainage_overlays": {item["id"]: {"paths": len(item["drainage_paths"]), "low_points": len(item["low_points"])} for item in project.drainage_reports},
            "section_previews": {item["id"]: {"name": item["name"], "samples": len(item["samples"])} for item in project.sections},
            "boundary_previews": {item["id"]: {"name": item["name"], "type": item["boundary_type"], "area": item["area"]} for item in project.boundaries},
            "engineering_diagnostics": project.diagnostics.to_dict(),
        }
        return project.visualization_metadata

    def refresh_diagnostics(self, project=None):
        project = project or self.ensure_project()
        project.diagnostics = SiteDiagnostics(
            len(self.projects),
            len(project.grading_operations),
            len(project.volume_reports),
            len(project.slope_reports),
            len(project.drainage_reports),
            len(project.sections),
            len(project.profiles),
            len(project.boundaries),
            len(project.validation_report.issues),
        )
        return project.diagnostics

    def to_dict(self):
        return {
            "active_project_id": self.active_project_id,
            "projects": [project.to_dict() for project in self.projects],
            "infrastructure": self.infrastructure_manager.to_dict(),
        }

    def from_dict(self, data):
        data = data or {}
        self.projects = [SiteProject.from_dict(item) for item in data.get("projects", [])]
        self.active_project_id = data.get("active_project_id") or (self.projects[-1].id if self.projects else None)
        self.infrastructure_manager.from_dict(data.get("infrastructure", {}))

    def clear(self):
        self.projects.clear()
        self.active_project_id = None
        self.infrastructure_manager.clear()

    def _sample_line(self, surface, line, interval=None):
        if len(line) < 2:
            raise ValueError("Section/profile line requires two points.")
        start, end = line[0], line[-1]
        length = _distance2(start, end)
        interval = max(_f(interval, self.ensure_project().settings.station_interval), 1e-9)
        count = max(1, int(math.ceil(length / interval)))
        samples = []
        for i in range(count + 1):
            t = i / count
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t
            samples.append({"station": length * t, "point": [x, y, self.terrain_manager.elevation_at(surface, x, y)]})
        return samples


def _graded_elevation(point, old_z, grading_type, region, parameters):
    kind = grading_type.lower().replace("_", " ")
    if kind in {"pad", "building platform", "manual"}:
        if "elevation" in parameters:
            return _f(parameters["elevation"])
        return _f(region.get("elevation"), old_z)
    if kind == "road":
        centerline = parameters.get("centerline") or region.get("centerline")
        if not centerline or len(centerline) < 2:
            raise ValueError("Road grading requires a centerline.")
        start, end = centerline[0], centerline[-1]
        base_start = _f(parameters.get("start_elevation"), start[2] if len(start) > 2 else old_z)
        base_end = _f(parameters.get("end_elevation"), end[2] if len(end) > 2 else base_start)
        station_t = _project_fraction(point, start, end)
        crown = base_start + (base_end - base_start) * station_t
        cross_slope = _f(parameters.get("cross_slope"), 0.0) / 100.0
        offset = _signed_offset(point, start, end)
        return crown + offset * cross_slope
    if kind == "slope":
        start = parameters.get("start") or region.get("start")
        end = parameters.get("end") or region.get("end")
        if not start or not end:
            raise ValueError("Slope grading requires start and end control points.")
        return _linear_grade(point, start, end)
    if kind == "automatic":
        constraints = parameters.get("constraints") or []
        if not constraints:
            raise ValueError("Automatic grading requires constraint control points.")
        weighted, weights = 0.0, 0.0
        for control in constraints:
            dist2 = (point[0] - control[0]) ** 2 + (point[1] - control[1]) ** 2
            if dist2 <= 1e-12:
                return _f(control[2])
            weight = 1.0 / dist2
            weighted += _f(control[2]) * weight
            weights += weight
        return weighted / weights
    if kind == "grade breakline":
        breakline = parameters.get("breakline") or []
        if len(breakline) < 2:
            raise ValueError("Grade breakline requires at least two control points.")
        nearest = min(zip(breakline, breakline[1:]), key=lambda seg: _distance_point_to_segment(point, seg[0], seg[1]))
        return _linear_grade(point, nearest[0], nearest[1])
    raise ValueError(f"Unsupported grading type '{grading_type}'.")


def _point_in_region(point, region):
    if not region:
        return True
    if "bounds" in region:
        xmin, ymin, xmax, ymax = region["bounds"]
        return xmin <= point[0] <= xmax and ymin <= point[1] <= ymax
    if "polygon" in region:
        return _point_in_polygon(point, region["polygon"])
    if "center" in region and "radius" in region:
        center = region["center"]
        return math.hypot(point[0] - center[0], point[1] - center[1]) <= _f(region["radius"])
    return True


def _point_in_polygon(point, polygon):
    x, y = point[0], point[1]
    inside = False
    count = len(polygon)
    for i in range(count):
        x1, y1 = polygon[i][:2]
        x2, y2 = polygon[(i + 1) % count][:2]
        crosses = (y1 > y) != (y2 > y)
        if crosses and x < (x2 - x1) * (y - y1) / max(y2 - y1, 1e-12) + x1:
            inside = not inside
    return inside


def _polygon_area(polygon):
    total = 0.0
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        total += a[0] * b[1] - b[0] * a[1]
    return abs(total) * 0.5


def _distance2(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _project_fraction(point, start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    denom = dx * dx + dy * dy
    if denom <= 1e-12:
        return 0.0
    return max(0.0, min(1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / denom))


def _signed_offset(point, start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = max(math.hypot(dx, dy), 1e-12)
    return ((point[0] - start[0]) * -dy + (point[1] - start[1]) * dx) / length


def _linear_grade(point, start, end):
    t = _project_fraction(point, start, end)
    return _f(start[2]) + (_f(end[2]) - _f(start[2])) * t


def _distance_point_to_segment(point, start, end):
    t = _project_fraction(point, start, end)
    px = start[0] + (end[0] - start[0]) * t
    py = start[1] + (end[1] - start[1]) * t
    return math.hypot(point[0] - px, point[1] - py)


def _triangle_area_xy(points):
    a, b, c = points
    return abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) * 0.5


def _earthwork_volumes(existing_points, design_points, triangles, region):
    cut = fill = area_total = 0.0
    for tri in triangles:
        ep = [existing_points[i] for i in tri]
        dp = [design_points[i] for i in tri]
        centroid = [sum(p[0] for p in ep) / 3.0, sum(p[1] for p in ep) / 3.0, 0.0]
        if region and not _point_in_region(centroid, region):
            continue
        area = _triangle_area_xy(ep)
        delta = sum(dp[i][2] - ep[i][2] for i in range(3)) / 3.0
        volume = area * delta
        if volume >= 0.0:
            fill += volume
        else:
            cut += abs(volume)
        area_total += area
    return cut, fill, area_total


def _sample_design_on_existing(existing, design):
    points = []
    terrain = None
    for point in existing.points:
        points.append([point[0], point[1], _interpolate(design.points, point[0], point[1])])
    return points


def _interpolate(points, x, y):
    weighted = weights = 0.0
    for px, py, pz in points:
        dist2 = (px - x) ** 2 + (py - y) ** 2
        if dist2 <= 1e-12:
            return pz
        weight = 1.0 / dist2
        weighted += pz * weight
        weights += weight
    return weighted / weights if weights else 0.0


def _triangle_slope_percent(points):
    a, b, c = points
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    horizontal = math.hypot(nx, ny)
    return abs(horizontal / max(abs(nz), 1e-12)) * 100.0


def _slope_colors(classes):
    palette = ["#2e7d32", "#66bb6a", "#fdd835", "#fb8c00", "#e53935", "#8e24aa", "#4a148c"]
    return {str(cls): palette[idx % len(palette)] for idx, cls in enumerate(classes)}


def _surface_neighbors(triangles, point_count):
    neighbors = {idx: set() for idx in range(point_count)}
    for a, b, c in triangles:
        neighbors[a].update([b, c])
        neighbors[b].update([a, c])
        neighbors[c].update([a, b])
    return neighbors


def _drainage_path(start, points, flow_to):
    path = [list(points[start])]
    seen = {start}
    current = start
    while flow_to[current] is not None and flow_to[current] not in seen:
        current = flow_to[current]
        seen.add(current)
        path.append(list(points[current]))
    return path


def _catchment_areas(surface, flow_to):
    low_for = {}
    for idx in range(len(surface.points)):
        current = idx
        seen = set()
        while flow_to[current] is not None and current not in seen:
            seen.add(current)
            current = flow_to[current]
        low_for[idx] = current
    areas = {}
    for tri in surface.triangles:
        area = _triangle_area_xy([surface.points[i] for i in tri])
        low = low_for[min(tri, key=lambda i: surface.points[i][2])]
        areas[str(low)] = areas.get(str(low), 0.0) + area
    return areas

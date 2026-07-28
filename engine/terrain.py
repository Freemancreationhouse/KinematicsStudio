import json
import math
import struct
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from engine.geometry import Edge, Face, MeshData, Vector3, Vertex


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
class TerrainSettings:
    """Editable terrain modeling settings."""

    default_surface_type: str = "TIN"
    contour_minor_interval: float = 1.0
    contour_major_interval: float = 5.0
    interpolation: str = "inverse_distance"
    lod_levels: list = field(default_factory=lambda: [1, 2, 4, 8])
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "default_surface_type": self.default_surface_type,
            "contour_minor_interval": self.contour_minor_interval,
            "contour_major_interval": self.contour_major_interval,
            "interpolation": self.interpolation,
            "lod_levels": list(self.lod_levels),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return TerrainSettings(
            data.get("default_surface_type", "TIN"),
            _f(data.get("contour_minor_interval"), 1.0),
            _f(data.get("contour_major_interval"), 5.0),
            data.get("interpolation", "inverse_distance"),
            list(data.get("lod_levels", [1, 2, 4, 8])),
            dict(data.get("metadata", {})),
        )


@dataclass
class TerrainSurface:
    """Editable terrain surface source data; geometry is owned by BodyManager only."""

    name: str
    surface_type: str
    points: list = field(default_factory=list)
    triangles: list = field(default_factory=list)
    grid: dict = field(default_factory=dict)
    boundary: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    body_reference: dict = field(default_factory=dict)
    lod_metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "surface_type": self.surface_type,
            "points": [list(point) for point in self.points],
            "triangles": [list(triangle) for triangle in self.triangles],
            "grid": dict(self.grid),
            "boundary": [list(point) for point in self.boundary],
            "metadata": dict(self.metadata),
            "body_reference": dict(self.body_reference),
            "lod_metadata": dict(self.lod_metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return TerrainSurface(
            data.get("name", "Terrain Surface"),
            data.get("surface_type", "TIN"),
            [list(point) for point in data.get("points", [])],
            [list(triangle) for triangle in data.get("triangles", [])],
            dict(data.get("grid", {})),
            [list(point) for point in data.get("boundary", [])],
            dict(data.get("metadata", {})),
            dict(data.get("body_reference", {})),
            dict(data.get("lod_metadata", {})),
            data.get("id", str(uuid4())),
        )

    def bounds(self):
        if not self.points:
            return None
        xs = [point[0] for point in self.points]
        ys = [point[1] for point in self.points]
        zs = [point[2] for point in self.points]
        return [min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)]

    def mesh_data(self):
        vertices = [Vertex(Vector3(point[0], point[1], point[2])) for point in self.points]
        edges = set()
        faces = []
        for triangle in self.triangles:
            if len(triangle) != 3:
                continue
            a, b, c = triangle
            faces.append(Face([a, b, c]))
            edges.update({tuple(sorted((a, b))), tuple(sorted((b, c))), tuple(sorted((c, a)))})
        return MeshData(vertices, [Edge(a, b) for a, b in sorted(edges)], faces)


@dataclass
class TerrainContour:
    """Generated terrain contour metadata."""

    elevation: float
    contour_type: str
    polylines: list = field(default_factory=list)
    labels: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        return {
            "id": self.id,
            "elevation": self.elevation,
            "contour_type": self.contour_type,
            "polylines": [[list(point) for point in line] for line in self.polylines],
            "labels": [dict(item) for item in self.labels],
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return TerrainContour(
            _f(data.get("elevation")),
            data.get("contour_type", "Minor"),
            [[list(point) for point in line] for line in data.get("polylines", [])],
            [dict(item) for item in data.get("labels", [])],
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class TerrainValidationReport:
    """Terrain validation report."""

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
        return TerrainValidationReport(
            bool(data.get("valid", True)),
            list(data.get("issues", [])),
            list(data.get("warnings", [])),
            dict(data.get("statistics", {})),
            data.get("generated_at", _timestamp()),
        )


@dataclass
class TerrainDiagnostics:
    """Terrain diagnostics summary."""

    projects: int = 0
    surfaces: int = 0
    points: int = 0
    triangles: int = 0
    contours: int = 0
    edits: int = 0
    validation_issues: int = 0
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        data = data or {}
        return TerrainDiagnostics(
            int(data.get("projects", 0)),
            int(data.get("surfaces", 0)),
            int(data.get("points", 0)),
            int(data.get("triangles", 0)),
            int(data.get("contours", 0)),
            int(data.get("edits", 0)),
            int(data.get("validation_issues", 0)),
            data.get("updated_at", _timestamp()),
        )


@dataclass
class TerrainProject:
    """Terrain project stored under the existing GIS workspace."""

    name: str = "Terrain Project"
    settings: TerrainSettings = field(default_factory=TerrainSettings)
    surfaces: list = field(default_factory=list)
    contours: list = field(default_factory=list)
    edit_history: list = field(default_factory=list)
    analysis_results: dict = field(default_factory=dict)
    indexes: dict = field(default_factory=dict)
    visualization_metadata: dict = field(default_factory=dict)
    validation_report: TerrainValidationReport = field(default_factory=TerrainValidationReport)
    diagnostics: TerrainDiagnostics = field(default_factory=TerrainDiagnostics)
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "settings": self.settings.to_dict(),
            "surfaces": [surface.to_dict() for surface in self.surfaces],
            "contours": [contour.to_dict() for contour in self.contours],
            "edit_history": [dict(item) for item in self.edit_history],
            "analysis_results": dict(self.analysis_results),
            "indexes": dict(self.indexes),
            "visualization_metadata": dict(self.visualization_metadata),
            "validation_report": self.validation_report.to_dict(),
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return TerrainProject(
            data.get("name", "Terrain Project"),
            TerrainSettings.from_dict(data.get("settings", {})),
            [TerrainSurface.from_dict(item) for item in data.get("surfaces", [])],
            [TerrainContour.from_dict(item) for item in data.get("contours", [])],
            [dict(item) for item in data.get("edit_history", [])],
            dict(data.get("analysis_results", {})),
            dict(data.get("indexes", {})),
            dict(data.get("visualization_metadata", {})),
            TerrainValidationReport.from_dict(data.get("validation_report", {})),
            TerrainDiagnostics.from_dict(data.get("diagnostics", {})),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


class TerrainManager:
    """GIS-scoped terrain modeling manager."""

    def __init__(self, gis_manager=None):
        self.gis_manager = gis_manager
        self.projects = []
        self.active_project_id = None
        from engine.site_engineering import SiteEngineeringManager
        self.site_engineering_manager = SiteEngineeringManager(self)
        self.site_engineering = self.site_engineering_manager

    @property
    def active_project(self):
        if not self.projects:
            return None
        return self.get_project(self.active_project_id) or self.projects[-1]

    def create_project(self, name="Terrain Project", settings=None, metadata=None):
        project = TerrainProject(name, settings if isinstance(settings, TerrainSettings) else TerrainSettings.from_dict(settings or {}), metadata=dict(metadata or {}))
        self.projects.append(project)
        self.active_project_id = project.id
        self.refresh_diagnostics(project)
        return project

    def get_project(self, project):
        if isinstance(project, TerrainProject):
            return project if project in self.projects else None
        return next((item for item in self.projects if item.id == project or item.name == project), None)

    def ensure_project(self):
        return self.active_project or self.create_project()

    def add_surface(self, surface):
        project = self.ensure_project()
        if surface not in project.surfaces:
            project.surfaces.append(surface)
        self.rebuild_indexes(project)
        self.refresh_diagnostics(project)
        return surface

    def remove_surface(self, surface):
        project = self.active_project
        if project and surface in project.surfaces:
            project.surfaces.remove(surface)
            project.contours = [contour for contour in project.contours if contour.metadata.get("surface_id") != surface.id]
            self.rebuild_indexes(project)
            self.refresh_diagnostics(project)
            return True
        return False

    def surface_for(self, surface):
        project = self.active_project
        if project is None:
            return None
        if isinstance(surface, TerrainSurface):
            return surface if surface in project.surfaces else None
        return next((item for item in project.surfaces if item.id == surface or item.name == surface), None)

    def import_terrain(self, path, name=None, terrain_type=None):
        source = Path(path)
        if not source.exists():
            raise FileNotFoundError(str(source))
        suffix = source.suffix.lower()
        if terrain_type:
            kind = terrain_type.upper()
        elif suffix in (".asc", ".grd"):
            kind = "ASCII Grid"
        elif suffix in (".xyz", ".pts", ".csv"):
            kind = "XYZ Point Cloud"
        elif suffix in (".tin", ".json"):
            kind = "TIN"
        elif suffix in (".tif", ".tiff"):
            kind = "GeoTIFF"
        elif suffix in (".pgm",):
            kind = "Height Map"
        elif suffix in (".dem",):
            kind = "DEM"
        else:
            raise ValueError(f"Unsupported terrain format '{suffix}'.")
        if kind == "ASCII Grid":
            surface = self._from_ascii_grid(source, name)
        elif kind == "XYZ Point Cloud":
            surface = self._from_xyz(source, name)
        elif kind == "TIN":
            surface = self._from_tin(source, name)
        elif kind == "GeoTIFF":
            surface = self._from_geotiff(source, name)
        elif kind == "Height Map":
            surface = self._from_pgm(source, name)
        elif kind == "DEM":
            surface = self._from_dem(source, name)
        else:
            raise ValueError(f"Unsupported terrain type '{kind}'.")
        surface.metadata.update({"source_path": str(source), "source_type": kind, "imported_at": _timestamp()})
        self.add_surface(surface)
        return surface

    def create_from_points(self, name, points, method="TIN"):
        pts = [list(map(float, point[:3])) for point in points if len(point) >= 3]
        if len(pts) < 3:
            raise ValueError("Terrain point reconstruction requires at least three XYZ points.")
        surface = TerrainSurface(name, method, pts, _triangulate_grid_or_fan(pts), metadata={"generation": "point_reconstruction"})
        self.add_surface(surface)
        return surface

    def edit_surface(self, surface, operation, region=None, amount=0.0, elevation=None, radius=1.0, strength=1.0):
        target = self.surface_for(surface)
        if target is None:
            raise ValueError("Terrain surface not found.")
        before = [list(point) for point in target.points]
        region = region or {}
        if operation == "refine":
            self.refine_surface(target)
            target.metadata["last_edit"] = {"operation": operation, "timestamp": _timestamp()}
            self.ensure_project().edit_history.append({"surface_id": target.id, "operation": operation, "before_count": len(before), "after_count": len(target.points), "timestamp": _timestamp()})
            self.refresh_diagnostics()
            return before
        if operation == "boundary":
            boundary = region.get("boundary")
            if not isinstance(boundary, list) or len(boundary) < 3:
                raise ValueError("Boundary editing requires at least three boundary points.")
            target.boundary = [list(map(float, point[:2])) for point in boundary]
            target.metadata["last_edit"] = {"operation": operation, "timestamp": _timestamp()}
            self.ensure_project().edit_history.append({"surface_id": target.id, "operation": operation, "before_count": len(before), "after_count": len(target.points), "timestamp": _timestamp()})
            self.refresh_diagnostics()
            return before
        for index, point in enumerate(target.points):
            if not _point_in_region(point, region):
                continue
            if operation == "raise":
                point[2] += float(amount)
            elif operation == "lower":
                point[2] -= float(amount)
            elif operation == "flatten":
                point[2] = float(elevation if elevation is not None else amount)
            elif operation == "grade":
                start = region.get("start", [point[0], point[1], point[2]])
                end = region.get("end", [point[0] + 1.0, point[1], point[2]])
                point[2] = _grade_elevation(point, start, end)
            elif operation == "sculpt":
                center = region.get("center", [point[0], point[1]])
                dist = math.hypot(point[0] - center[0], point[1] - center[1])
                if dist <= radius:
                    point[2] += float(amount) * max(0.0, 1.0 - dist / max(radius, 1e-9)) * float(strength)
            elif operation == "smooth":
                continue
            else:
                raise ValueError(f"Unsupported terrain edit operation '{operation}'.")
        if operation == "smooth":
            target.points = _smooth_points(target.points, target.triangles, region, float(strength))
        target.metadata["last_edit"] = {"operation": operation, "timestamp": _timestamp()}
        self.ensure_project().edit_history.append({"surface_id": target.id, "operation": operation, "before_count": len(before), "after_count": len(target.points), "timestamp": _timestamp()})
        self.refresh_diagnostics()
        return before

    def rebuild_surface(self, surface):
        target = self.surface_for(surface)
        if target is None:
            raise ValueError("Terrain surface not found.")
        target.triangles = _triangulate_grid_or_fan(target.points)
        target.metadata["rebuilt_at"] = _timestamp()
        self.rebuild_indexes()
        self.refresh_diagnostics()
        return target

    def refine_surface(self, surface):
        target = self.surface_for(surface)
        if target is None:
            raise ValueError("Terrain surface not found.")
        midpoint_cache = {}
        points = [list(point) for point in target.points]
        triangles = []
        def midpoint(a, b):
            key = tuple(sorted((a, b)))
            if key in midpoint_cache:
                return midpoint_cache[key]
            pa, pb = points[a], points[b]
            points.append([(pa[0] + pb[0]) / 2.0, (pa[1] + pb[1]) / 2.0, (pa[2] + pb[2]) / 2.0])
            midpoint_cache[key] = len(points) - 1
            return midpoint_cache[key]
        for a, b, c in target.triangles:
            ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
            triangles.extend([[a, ab, ca], [ab, b, bc], [ca, bc, c], [ab, bc, ca]])
        target.points = points
        target.triangles = triangles
        target.lod_metadata["refined_at"] = _timestamp()
        self.rebuild_indexes()
        self.refresh_diagnostics()
        return target

    def generate_contours(self, surface, minor_interval=None, major_interval=None, smooth=False):
        target = self.surface_for(surface)
        if target is None:
            raise ValueError("Terrain surface not found.")
        project = self.ensure_project()
        minor = float(minor_interval or project.settings.contour_minor_interval)
        major = float(major_interval or project.settings.contour_major_interval)
        z_values = [point[2] for point in target.points]
        if not z_values:
            return []
        start = math.floor(min(z_values) / minor) * minor
        end = math.ceil(max(z_values) / minor) * minor
        contours = []
        level = start
        while level <= end + 1e-9:
            lines = _contour_triangles(target.points, target.triangles, level)
            if smooth:
                lines = [_smooth_line(line) for line in lines]
            if lines:
                contour_type = "Major" if abs((level / major) - round(level / major)) < 1e-8 else "Minor"
                labels = [{"text": f"{level:.2f}", "position": line[len(line) // 2]} for line in lines if line]
                contours.append(TerrainContour(level, contour_type, lines, labels, {"surface_id": target.id}))
            level += minor
        project.contours = [item for item in project.contours if item.metadata.get("surface_id") != target.id] + contours
        self.refresh_diagnostics(project)
        return contours

    def elevation_at(self, surface, x, y):
        target = self.surface_for(surface)
        if target is None:
            raise ValueError("Terrain surface not found.")
        return _interpolate_elevation(target.points, float(x), float(y))

    def slope_at(self, surface, x, y):
        dzdx, dzdy = self._gradient(surface, x, y)
        return math.degrees(math.atan(math.hypot(dzdx, dzdy)))

    def aspect_at(self, surface, x, y):
        dzdx, dzdy = self._gradient(surface, x, y)
        aspect = math.degrees(math.atan2(dzdy, -dzdx))
        return aspect + 360.0 if aspect < 0.0 else aspect

    def statistics(self, surface):
        target = self.surface_for(surface)
        if target is None:
            raise ValueError("Terrain surface not found.")
        zs = [point[2] for point in target.points]
        stats = {
            "points": len(target.points),
            "triangles": len(target.triangles),
            "min_elevation": min(zs) if zs else 0.0,
            "max_elevation": max(zs) if zs else 0.0,
            "mean_elevation": sum(zs) / len(zs) if zs else 0.0,
            "bounds": target.bounds(),
        }
        self.ensure_project().analysis_results[target.id] = stats
        return stats

    def validate_surface(self, surface):
        target = self.surface_for(surface)
        issues, warnings = [], []
        if target is None:
            return TerrainValidationReport(False, ["Terrain surface not found."], [], {})
        if len(target.points) < 3:
            issues.append(f"Terrain surface '{target.name}' requires at least three points.")
        for triangle in target.triangles:
            if len(triangle) != 3:
                issues.append(f"Terrain surface '{target.name}' has a non-triangular face.")
            for index in triangle:
                if index < 0 or index >= len(target.points):
                    issues.append(f"Terrain surface '{target.name}' references missing point index {index}.")
        if not target.triangles:
            issues.append(f"Terrain surface '{target.name}' has no TIN triangles.")
        if not target.body_reference:
            warnings.append(f"Terrain surface '{target.name}' has no BodyManager body reference yet.")
        return TerrainValidationReport(not issues, issues, warnings, self.statistics(target))

    def validate_project(self):
        project = self.ensure_project()
        issues, warnings = [], []
        names = set()
        for surface in project.surfaces:
            if surface.name in names:
                issues.append(f"Duplicate terrain surface name '{surface.name}'.")
            names.add(surface.name)
            report = self.validate_surface(surface)
            issues.extend(report.issues)
            warnings.extend(report.warnings)
        project.validation_report = TerrainValidationReport(not issues, issues, warnings, self.refresh_diagnostics(project).to_dict())
        return project.validation_report

    def rebuild_indexes(self, project=None):
        project = project or self.ensure_project()
        project.indexes = {
            "surfaces": {surface.id: {"name": surface.name, "bounds": surface.bounds()} for surface in project.surfaces},
            "contours": {contour.id: {"surface_id": contour.metadata.get("surface_id"), "elevation": contour.elevation} for contour in project.contours},
            "updated_at": _timestamp(),
        }
        return project.indexes

    def visualization_metadata(self):
        project = self.ensure_project()
        project.visualization_metadata = {
            "terrain_preview": {surface.id: {"name": surface.name, "bounds": surface.bounds(), "body_reference": dict(surface.body_reference)} for surface in project.surfaces},
            "contours": {contour.id: contour.to_dict() for contour in project.contours},
            "elevation_colors": {surface.id: {"min": self.statistics(surface)["min_elevation"], "max": self.statistics(surface)["max_elevation"]} for surface in project.surfaces},
            "wireframe": {surface.id: True for surface in project.surfaces},
            "shaded_terrain": {surface.id: True for surface in project.surfaces},
            "selection": {},
            "editing_previews": {surface.id: surface.metadata.get("last_edit", {}) for surface in project.surfaces},
            "lod_visualization": {surface.id: dict(surface.lod_metadata) for surface in project.surfaces},
            "diagnostics": project.diagnostics.to_dict(),
        }
        return project.visualization_metadata

    def refresh_diagnostics(self, project=None):
        project = project or self.ensure_project()
        project.diagnostics = TerrainDiagnostics(
            len(self.projects),
            len(project.surfaces),
            sum(len(surface.points) for surface in project.surfaces),
            sum(len(surface.triangles) for surface in project.surfaces),
            len(project.contours),
            len(project.edit_history),
            len(project.validation_report.issues),
        )
        return project.diagnostics

    def to_dict(self):
        return {
            "active_project_id": self.active_project_id,
            "projects": [project.to_dict() for project in self.projects],
            "site_engineering": self.site_engineering_manager.to_dict(),
        }

    def from_dict(self, data):
        data = data or {}
        self.projects = [TerrainProject.from_dict(item) for item in data.get("projects", [])]
        self.active_project_id = data.get("active_project_id") or (self.projects[-1].id if self.projects else None)
        self.site_engineering_manager.from_dict(data.get("site_engineering", {}))

    def clear(self):
        self.projects.clear()
        self.active_project_id = None
        self.site_engineering_manager.clear()

    def _gradient(self, surface, x, y):
        delta = max(self.statistics(surface)["max_elevation"] - self.statistics(surface)["min_elevation"], 1.0) * 0.01
        z1 = self.elevation_at(surface, x - delta, y)
        z2 = self.elevation_at(surface, x + delta, y)
        z3 = self.elevation_at(surface, x, y - delta)
        z4 = self.elevation_at(surface, x, y + delta)
        return (z2 - z1) / (2 * delta), (z4 - z3) / (2 * delta)

    def _from_ascii_grid(self, path, name=None):
        lines = path.read_text(encoding="utf-8").splitlines()
        header = {}
        values_start = 0
        for idx, line in enumerate(lines[:10]):
            parts = line.split()
            if len(parts) >= 2 and parts[0].lower() in {"ncols", "nrows", "xllcorner", "yllcorner", "xllcenter", "yllcenter", "cellsize", "nodata_value"}:
                header[parts[0].lower()] = _f(parts[1])
                values_start = idx + 1
        ncols, nrows = int(header["ncols"]), int(header["nrows"])
        cell = header.get("cellsize", 1.0)
        x0 = header.get("xllcorner", header.get("xllcenter", 0.0))
        y0 = header.get("yllcorner", header.get("yllcenter", 0.0))
        nodata = header.get("nodata_value")
        rows = [[_f(value) for value in line.split()] for line in lines[values_start:values_start + nrows]]
        points = []
        index = {}
        for row in range(nrows):
            for col in range(ncols):
                z = rows[row][col]
                if nodata is not None and z == nodata:
                    continue
                index[(row, col)] = len(points)
                points.append([x0 + col * cell, y0 + (nrows - 1 - row) * cell, z])
        triangles = []
        for row in range(nrows - 1):
            for col in range(ncols - 1):
                keys = [(row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1)]
                if all(key in index for key in keys):
                    a, b, c, d = [index[key] for key in keys]
                    triangles.extend([[a, b, c], [b, d, c]])
        return TerrainSurface(name or path.stem, "Grid", points, triangles, {"ncols": ncols, "nrows": nrows, "cellsize": cell, "origin": [x0, y0]}, metadata={"format": "ASCII Grid"})

    def _from_xyz(self, path, name=None):
        points = []
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.replace(",", " ").split()
            if len(parts) >= 3:
                points.append([_f(parts[0]), _f(parts[1]), _f(parts[2])])
        return TerrainSurface(name or path.stem, "TIN", points, _triangulate_grid_or_fan(points), metadata={"format": "XYZ Point Cloud"})

    def _from_tin(self, path, name=None):
        data = json.loads(path.read_text(encoding="utf-8"))
        points = [list(map(float, point[:3])) for point in data.get("points", [])]
        triangles = [list(map(int, tri[:3])) for tri in data.get("triangles", [])]
        if not triangles:
            triangles = _triangulate_grid_or_fan(points)
        return TerrainSurface(name or data.get("name") or path.stem, "TIN", points, triangles, metadata={"format": "TIN"})

    def _from_pgm(self, path, name=None):
        magic, width, height, max_value, values = _read_pgm_height_map(path.read_bytes())
        points = [[col, height - 1 - row, values[row * width + col] / max(max_value, 1)] for row in range(height) for col in range(width)]
        triangles = _grid_triangles(width, height)
        return TerrainSurface(name or path.stem, "Grid", points, triangles, {"ncols": width, "nrows": height, "cellsize": 1.0}, metadata={"format": "Height Map", "height_map_encoding": magic})

    def _from_dem(self, path, name=None):
        return self._from_ascii_grid(path, name or path.stem)

    def _from_geotiff(self, path, name=None):
        width, height, values, metadata = _read_geotiff_elevations(path)
        scale = metadata.get("pixel_scale", [1.0, 1.0, 1.0])
        tie = metadata.get("tiepoint", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        x0, y0 = tie[3], tie[4]
        points = []
        for row in range(height):
            for col in range(width):
                points.append([x0 + col * scale[0], y0 - row * scale[1], values[row * width + col] * scale[2]])
        return TerrainSurface(name or path.stem, "Grid", points, _grid_triangles(width, height), {"ncols": width, "nrows": height, "cellsize": scale[0]}, metadata={"format": "GeoTIFF", "geotiff": metadata})


def _grid_triangles(width, height):
    triangles = []
    for row in range(height - 1):
        for col in range(width - 1):
            a = row * width + col
            b = a + 1
            c = a + width
            d = c + 1
            triangles.extend([[a, b, c], [b, d, c]])
    return triangles


def _triangulate_grid_or_fan(points):
    if len(points) < 3:
        return []
    xs = sorted({point[0] for point in points})
    ys = sorted({point[1] for point in points})
    if len(xs) * len(ys) == len(points):
        lookup = {(point[0], point[1]): idx for idx, point in enumerate(points)}
        triangles = []
        for yi in range(len(ys) - 1):
            for xi in range(len(xs) - 1):
                keys = [(xs[xi], ys[yi]), (xs[xi + 1], ys[yi]), (xs[xi], ys[yi + 1]), (xs[xi + 1], ys[yi + 1])]
                if all(key in lookup for key in keys):
                    a, b, c, d = [lookup[key] for key in keys]
                    triangles.extend([[a, b, c], [b, d, c]])
        if triangles:
            return triangles
    center = min(range(len(points)), key=lambda idx: (points[idx][0], points[idx][1]))
    ordered = sorted([idx for idx in range(len(points)) if idx != center], key=lambda idx: math.atan2(points[idx][1] - points[center][1], points[idx][0] - points[center][0]))
    return [[center, ordered[i], ordered[(i + 1) % len(ordered)]] for i in range(len(ordered))]


def _point_in_region(point, region):
    if not region:
        return True
    if "bounds" in region:
        xmin, ymin, xmax, ymax = region["bounds"]
        return xmin <= point[0] <= xmax and ymin <= point[1] <= ymax
    if "center" in region and "radius" in region:
        return math.hypot(point[0] - region["center"][0], point[1] - region["center"][1]) <= float(region["radius"])
    return True


def _grade_elevation(point, start, end):
    sx, sy, sz = start[:3]
    ex, ey, ez = end[:3]
    vx, vy = ex - sx, ey - sy
    length2 = vx * vx + vy * vy
    if length2 <= 1e-12:
        return sz
    t = max(0.0, min(1.0, ((point[0] - sx) * vx + (point[1] - sy) * vy) / length2))
    return sz + (ez - sz) * t


def _smooth_points(points, triangles, region, strength):
    neighbors = {idx: set() for idx in range(len(points))}
    for a, b, c in triangles:
        neighbors[a].update([b, c])
        neighbors[b].update([a, c])
        neighbors[c].update([a, b])
    updated = [list(point) for point in points]
    for idx, point in enumerate(points):
        if not _point_in_region(point, region) or not neighbors[idx]:
            continue
        avg = sum(points[n][2] for n in neighbors[idx]) / len(neighbors[idx])
        updated[idx][2] = point[2] * (1 - strength) + avg * strength
    return updated


def _interpolate_elevation(points, x, y):
    weighted, weights = 0.0, 0.0
    for px, py, pz in points:
        dist2 = (px - x) ** 2 + (py - y) ** 2
        if dist2 <= 1e-12:
            return pz
        weight = 1.0 / dist2
        weighted += pz * weight
        weights += weight
    return weighted / weights if weights else 0.0


def _contour_triangles(points, triangles, level):
    lines = []
    for triangle in triangles:
        tri = [points[index] for index in triangle]
        intersections = []
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            za, zb = a[2], b[2]
            if (za <= level <= zb or zb <= level <= za) and abs(zb - za) > 1e-12:
                t = (level - za) / (zb - za)
                intersections.append([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, level])
        if len(intersections) == 2:
            lines.append(intersections)
    return lines


def _smooth_line(line):
    if len(line) < 3:
        return line
    result = [line[0]]
    for idx in range(1, len(line) - 1):
        prev_pt, pt, next_pt = line[idx - 1], line[idx], line[idx + 1]
        result.append([(prev_pt[0] + pt[0] + next_pt[0]) / 3, (prev_pt[1] + pt[1] + next_pt[1]) / 3, pt[2]])
    result.append(line[-1])
    return result


def _read_pgm_height_map(data):
    def read_token(offset):
        while offset < len(data):
            byte = data[offset]
            if byte == 35:
                while offset < len(data) and data[offset] not in (10, 13):
                    offset += 1
            elif chr(byte).isspace():
                offset += 1
            else:
                break
        start = offset
        while offset < len(data) and not chr(data[offset]).isspace():
            offset += 1
        if start == offset:
            raise ValueError("Invalid PGM height map header.")
        return data[start:offset].decode("ascii"), offset

    magic, offset = read_token(0)
    if magic not in ("P2", "P5"):
        raise ValueError("Height map PGM must be P2 or P5.")
    width_token, offset = read_token(offset)
    height_token, offset = read_token(offset)
    max_token, offset = read_token(offset)
    width, height, max_value = int(width_token), int(height_token), int(max_token)
    if width <= 0 or height <= 0 or max_value <= 0:
        raise ValueError("PGM height map dimensions and maximum value must be positive.")
    if magic == "P2":
        values = []
        for _ in range(width * height):
            token, offset = read_token(offset)
            values.append(int(token))
        return magic, width, height, max_value, values
    while offset < len(data) and chr(data[offset]).isspace():
        offset += 1
    bytes_per_sample = 1 if max_value < 256 else 2
    expected = width * height * bytes_per_sample
    raw = data[offset:offset + expected]
    if len(raw) != expected:
        raise ValueError("PGM height map data is incomplete.")
    values = list(raw) if bytes_per_sample == 1 else [int.from_bytes(raw[i:i + 2], "big") for i in range(0, len(raw), 2)]
    return magic, width, height, max_value, values


def _read_geotiff_elevations(path):
    data = Path(path).read_bytes()
    endian = "<" if data[:2] == b"II" else ">"
    if data[:2] not in (b"II", b"MM"):
        raise ValueError("Invalid TIFF byte order.")
    if struct.unpack(endian + "H", data[2:4])[0] != 42:
        raise ValueError("Unsupported TIFF version.")
    ifd_offset = struct.unpack(endian + "I", data[4:8])[0]
    count = struct.unpack(endian + "H", data[ifd_offset:ifd_offset + 2])[0]
    tags = {}
    for idx in range(count):
        off = ifd_offset + 2 + idx * 12
        tag, typ, num, value = struct.unpack(endian + "HHII", data[off:off + 12])
        tags[tag] = (typ, num, value)
    width = int(_tag_value(data, endian, tags[256])[0])
    height = int(_tag_value(data, endian, tags[257])[0])
    bits = int(_tag_value(data, endian, tags.get(258, (3, 1, 16)))[0])
    sample_format = int(_tag_value(data, endian, tags.get(339, (3, 1, 1)))[0])
    strip_offsets = [int(value) for value in _tag_value(data, endian, tags[273])]
    strip_counts = [int(value) for value in _tag_value(data, endian, tags[279])]
    compression = int(_tag_value(data, endian, tags.get(259, (3, 1, 1)))[0])
    if compression != 1:
        raise ValueError("Only uncompressed GeoTIFF terrain rasters are supported.")
    raw = b"".join(data[offset:offset + count] for offset, count in zip(strip_offsets, strip_counts))
    fmt = {8: "B", 16: "H", 32: "f" if sample_format == 3 else "I"}[bits]
    size = struct.calcsize(endian + fmt)
    values = [float(struct.unpack(endian + fmt, raw[i:i + size])[0]) for i in range(0, min(len(raw), width * height * size), size)]
    if len(values) != width * height:
        raise ValueError("GeoTIFF raster data is incomplete.")
    metadata = {}
    if 33550 in tags:
        metadata["pixel_scale"] = list(_tag_value(data, endian, tags[33550]))
    if 33922 in tags:
        metadata["tiepoint"] = list(_tag_value(data, endian, tags[33922]))
    return width, height, values, metadata


def _tag_value(data, endian, tag_tuple):
    typ, count, value = tag_tuple
    sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 11: 4, 12: 8}
    fmts = {1: "B", 2: "c", 3: "H", 4: "I", 11: "f", 12: "d"}
    size = sizes[typ] * count
    raw = struct.pack(endian + "I", value)[:size] if size <= 4 else data[value:value + size]
    if typ == 2:
        return [raw.rstrip(b"\x00").decode("utf-8", errors="ignore")]
    return struct.unpack(endian + f"{count}{fmts[typ]}", raw)

import csv
import json
import math
import struct
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree

from engine.terrain import TerrainManager


WGS84_A = 6378137.0
WGS84_F = 1.0 / 298.257223563
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)
UTM_K0 = 0.9996


def _utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def _as_float(value, default=0.0):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _deep_coordinates(values):
    if not isinstance(values, (list, tuple)):
        return []
    if values and all(isinstance(item, (int, float)) for item in values[:2]):
        return [list(values)]
    result = []
    for item in values:
        result.extend(_deep_coordinates(item))
    return result


def _bounds_for_coordinates(coordinates):
    points = _deep_coordinates(coordinates)
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points if len(point) > 2]
    bounds = [min(xs), min(ys), max(xs), max(ys)]
    if zs:
        bounds.extend([min(zs), max(zs)])
    return bounds


@dataclass
class CRSDefinition:
    """Coordinate reference system definition used by GIS projects."""

    code: str
    name: str
    crs_type: str
    datum: str = "WGS84"
    unit: str = "meter"
    axes: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "crs_type": self.crs_type,
            "datum": self.datum,
            "unit": self.unit,
            "axes": [dict(item) for item in self.axes],
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return CRSDefinition(
            data.get("code", "EPSG:4326"),
            data.get("name", "WGS 84"),
            data.get("crs_type", "geographic"),
            data.get("datum", "WGS84"),
            data.get("unit", "degree"),
            [dict(item) for item in data.get("axes", [])],
            dict(data.get("metadata", {})),
        )


@dataclass
class GISCoordinate:
    """Coordinate value tagged with a CRS."""

    x: float
    y: float
    z: float = 0.0
    crs: str = "EPSG:4326"

    def to_dict(self):
        return {"x": self.x, "y": self.y, "z": self.z, "crs": self.crs}

    @staticmethod
    def from_dict(data):
        data = data or {}
        return GISCoordinate(
            _as_float(data.get("x")),
            _as_float(data.get("y")),
            _as_float(data.get("z")),
            data.get("crs", "EPSG:4326"),
        )


@dataclass
class GISFeature:
    """GIS feature storing coordinate data and attributes, not CAD geometry."""

    geometry_type: str
    coordinates: list
    attributes: dict = field(default_factory=dict)
    crs: str = "EPSG:4326"
    feature_class: str = ""
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def bounds(self):
        return _bounds_for_coordinates(self.coordinates)

    def to_dict(self):
        return {
            "id": self.id,
            "geometry_type": self.geometry_type,
            "coordinates": self.coordinates,
            "attributes": dict(self.attributes),
            "crs": self.crs,
            "feature_class": self.feature_class,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return GISFeature(
            data.get("geometry_type", "Point"),
            data.get("coordinates", []),
            dict(data.get("attributes", {})),
            data.get("crs", "EPSG:4326"),
            data.get("feature_class", ""),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class GISLayer:
    """Persistent GIS layer containing GIS features and layer display metadata."""

    name: str
    layer_type: str = "Vector"
    crs: str = "EPSG:4326"
    features: list = field(default_factory=list)
    visible: bool = True
    locked: bool = False
    group: str = ""
    metadata: dict = field(default_factory=dict)
    attribute_metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "layer_type": self.layer_type,
            "crs": self.crs,
            "features": [feature.to_dict() for feature in self.features],
            "visible": bool(self.visible),
            "locked": bool(self.locked),
            "group": self.group,
            "metadata": dict(self.metadata),
            "attribute_metadata": dict(self.attribute_metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return GISLayer(
            data.get("name", "GIS Layer"),
            data.get("layer_type", "Vector"),
            data.get("crs", "EPSG:4326"),
            [GISFeature.from_dict(item) for item in data.get("features", [])],
            bool(data.get("visible", True)),
            bool(data.get("locked", False)),
            data.get("group", ""),
            dict(data.get("metadata", {})),
            dict(data.get("attribute_metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class SurveyPoint:
    """Survey point, benchmark or control point metadata."""

    name: str
    coordinate: GISCoordinate
    point_type: str = "Survey Point"
    elevation: float = 0.0
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "coordinate": self.coordinate.to_dict(),
            "point_type": self.point_type,
            "elevation": float(self.elevation),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return SurveyPoint(
            data.get("name", "Survey Point"),
            GISCoordinate.from_dict(data.get("coordinate", {})),
            data.get("point_type", "Survey Point"),
            _as_float(data.get("elevation")),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class GISImportRecord:
    """GIS import result metadata."""

    file_path: str
    format_name: str
    layer_ids: list = field(default_factory=list)
    feature_count: int = 0
    crs: str = "EPSG:4326"
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    imported_at: str = field(default_factory=_utc_timestamp)

    def to_dict(self):
        return {
            "id": self.id,
            "file_path": self.file_path,
            "format_name": self.format_name,
            "layer_ids": list(self.layer_ids),
            "feature_count": int(self.feature_count),
            "crs": self.crs,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
            "imported_at": self.imported_at,
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return GISImportRecord(
            data.get("file_path", ""),
            data.get("format_name", ""),
            list(data.get("layer_ids", [])),
            int(data.get("feature_count", 0)),
            data.get("crs", "EPSG:4326"),
            list(data.get("errors", [])),
            list(data.get("warnings", [])),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
            data.get("imported_at", _utc_timestamp()),
        )


@dataclass
class GISValidationReport:
    """GIS validation report."""

    valid: bool = True
    issues: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    statistics: dict = field(default_factory=dict)
    generated_at: str = field(default_factory=_utc_timestamp)

    def to_dict(self):
        return {
            "valid": bool(self.valid),
            "issues": list(self.issues),
            "warnings": list(self.warnings),
            "statistics": dict(self.statistics),
            "generated_at": self.generated_at,
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return GISValidationReport(
            bool(data.get("valid", True)),
            list(data.get("issues", [])),
            list(data.get("warnings", [])),
            dict(data.get("statistics", {})),
            data.get("generated_at", _utc_timestamp()),
        )


@dataclass
class GISDiagnostics:
    """GIS workspace diagnostics."""

    projects: int = 0
    layers: int = 0
    features: int = 0
    survey_points: int = 0
    imports: int = 0
    crs_definitions: int = 0
    validation_issues: int = 0
    updated_at: str = field(default_factory=_utc_timestamp)

    def to_dict(self):
        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        data = data or {}
        return GISDiagnostics(
            int(data.get("projects", 0)),
            int(data.get("layers", 0)),
            int(data.get("features", 0)),
            int(data.get("survey_points", 0)),
            int(data.get("imports", 0)),
            int(data.get("crs_definitions", 0)),
            int(data.get("validation_issues", 0)),
            data.get("updated_at", _utc_timestamp()),
        )


@dataclass
class GISWorkspace:
    """GIS workspace extension stored by the existing Workspace."""

    active: bool = True
    project_id: str = ""
    preferences: dict = field(default_factory=dict)
    spatial_reference: dict = field(default_factory=dict)
    version_metadata: dict = field(default_factory=lambda: {"release": "2.0", "batch": "A"})

    def to_dict(self):
        return {
            "active": bool(self.active),
            "project_id": self.project_id,
            "preferences": dict(self.preferences),
            "spatial_reference": dict(self.spatial_reference),
            "version_metadata": dict(self.version_metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return GISWorkspace(
            bool(data.get("active", True)),
            data.get("project_id", ""),
            dict(data.get("preferences", {})),
            dict(data.get("spatial_reference", {})),
            dict(data.get("version_metadata", {"release": "2.0", "batch": "A"})),
        )


@dataclass
class GISProject:
    """Workspace-owned GIS project metadata and GIS feature storage."""

    name: str = "GIS Project"
    metadata: dict = field(default_factory=dict)
    default_crs: str = "EPSG:4326"
    local_origin: GISCoordinate = field(default_factory=lambda: GISCoordinate(0.0, 0.0, 0.0, "EPSG:4326"))
    workspace: GISWorkspace = field(default_factory=GISWorkspace)
    layers: list = field(default_factory=list)
    survey_points: list = field(default_factory=list)
    import_records: list = field(default_factory=list)
    validation_report: GISValidationReport = field(default_factory=GISValidationReport)
    diagnostics: GISDiagnostics = field(default_factory=GISDiagnostics)
    indexes: dict = field(default_factory=dict)
    visualization_metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "metadata": dict(self.metadata),
            "default_crs": self.default_crs,
            "local_origin": self.local_origin.to_dict(),
            "workspace": self.workspace.to_dict(),
            "layers": [layer.to_dict() for layer in self.layers],
            "survey_points": [point.to_dict() for point in self.survey_points],
            "import_records": [record.to_dict() for record in self.import_records],
            "validation_report": self.validation_report.to_dict(),
            "diagnostics": self.diagnostics.to_dict(),
            "indexes": dict(self.indexes),
            "visualization_metadata": dict(self.visualization_metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        project = GISProject(
            data.get("name", "GIS Project"),
            dict(data.get("metadata", {})),
            data.get("default_crs", "EPSG:4326"),
            GISCoordinate.from_dict(data.get("local_origin", {})),
            GISWorkspace.from_dict(data.get("workspace", {})),
            [GISLayer.from_dict(item) for item in data.get("layers", [])],
            [SurveyPoint.from_dict(item) for item in data.get("survey_points", [])],
            [GISImportRecord.from_dict(item) for item in data.get("import_records", [])],
            GISValidationReport.from_dict(data.get("validation_report", {})),
            GISDiagnostics.from_dict(data.get("diagnostics", {})),
            dict(data.get("indexes", {})),
            dict(data.get("visualization_metadata", {})),
            data.get("id", str(uuid4())),
        )
        if not project.workspace.project_id:
            project.workspace.project_id = project.id
        return project


class CoordinateSystemManagerGIS:
    """CRS registry and coordinate transformation service."""

    def __init__(self):
        self.registry = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register_crs(CRSDefinition("EPSG:4326", "WGS 84", "geographic", "WGS84", "degree", [
            {"name": "longitude", "direction": "east", "unit": "degree"},
            {"name": "latitude", "direction": "north", "unit": "degree"},
        ]))
        self.register_crs(CRSDefinition("EPSG:4978", "WGS 84 / ECEF", "geocentric", "WGS84", "meter", [
            {"name": "X", "direction": "geocentricX", "unit": "meter"},
            {"name": "Y", "direction": "geocentricY", "unit": "meter"},
            {"name": "Z", "direction": "geocentricZ", "unit": "meter"},
        ]))
        for zone in range(1, 61):
            self.register_crs(CRSDefinition(
                f"EPSG:{32600 + zone}",
                f"WGS 84 / UTM zone {zone}N",
                "projected",
                "WGS84",
                "meter",
                [{"name": "easting", "direction": "east", "unit": "meter"}, {"name": "northing", "direction": "north", "unit": "meter"}],
                {"projection": "UTM", "zone": zone, "hemisphere": "N"},
            ))
            self.register_crs(CRSDefinition(
                f"EPSG:{32700 + zone}",
                f"WGS 84 / UTM zone {zone}S",
                "projected",
                "WGS84",
                "meter",
                [{"name": "easting", "direction": "east", "unit": "meter"}, {"name": "northing", "direction": "north", "unit": "meter"}],
                {"projection": "UTM", "zone": zone, "hemisphere": "S"},
            ))

    def register_crs(self, definition):
        self.registry[definition.code.upper()] = definition
        return definition

    def get(self, code):
        return self.registry.get(str(code or "").upper())

    def validate(self, code):
        return self.get(code) is not None

    def transform(self, coordinate, target_crs):
        source = coordinate if isinstance(coordinate, GISCoordinate) else GISCoordinate.from_dict(coordinate)
        target = str(target_crs or "EPSG:4326").upper()
        if source.crs.upper() == target:
            return GISCoordinate(source.x, source.y, source.z, target)
        lon, lat, height = self._to_geographic(source)
        return self._from_geographic(lon, lat, height, target)

    def project_coordinates(self, coordinates, source_crs, target_crs):
        def project_node(node):
            if isinstance(node, (list, tuple)) and node and all(isinstance(item, (int, float)) for item in node[:2]):
                transformed = self.transform(GISCoordinate(node[0], node[1], node[2] if len(node) > 2 else 0.0, source_crs), target_crs)
                value = [transformed.x, transformed.y]
                if len(node) > 2:
                    value.append(transformed.z)
                return value
            return [project_node(item) for item in node]
        return project_node(coordinates)

    def to_dict(self):
        return {"registry": {code: definition.to_dict() for code, definition in self.registry.items()}}

    def from_dict(self, data):
        self.registry = {}
        self._register_defaults()
        for item in (data or {}).get("registry", {}).values():
            self.register_crs(CRSDefinition.from_dict(item))

    def _to_geographic(self, coordinate):
        definition = self.get(coordinate.crs)
        if definition is None:
            raise ValueError(f"Unsupported CRS '{coordinate.crs}'.")
        if definition.crs_type == "geographic":
            return coordinate.x, coordinate.y, coordinate.z
        if definition.crs_type == "geocentric":
            return self._ecef_to_wgs84(coordinate.x, coordinate.y, coordinate.z)
        if definition.metadata.get("projection") == "UTM":
            return self._utm_to_wgs84(coordinate.x, coordinate.y, definition.metadata["zone"], definition.metadata["hemisphere"], coordinate.z)
        raise ValueError(f"Unsupported CRS transform from '{coordinate.crs}'.")

    def _from_geographic(self, lon, lat, height, target_crs):
        definition = self.get(target_crs)
        if definition is None:
            raise ValueError(f"Unsupported CRS '{target_crs}'.")
        if definition.crs_type == "geographic":
            return GISCoordinate(lon, lat, height, definition.code)
        if definition.crs_type == "geocentric":
            x, y, z = self._wgs84_to_ecef(lon, lat, height)
            return GISCoordinate(x, y, z, definition.code)
        if definition.metadata.get("projection") == "UTM":
            easting, northing = self._wgs84_to_utm(lon, lat, definition.metadata["zone"], definition.metadata["hemisphere"])
            return GISCoordinate(easting, northing, height, definition.code)
        raise ValueError(f"Unsupported CRS transform to '{target_crs}'.")

    @staticmethod
    def _wgs84_to_ecef(lon, lat, height):
        lon_rad = math.radians(lon)
        lat_rad = math.radians(lat)
        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
        x = (n + height) * cos_lat * math.cos(lon_rad)
        y = (n + height) * cos_lat * math.sin(lon_rad)
        z = (n * (1.0 - WGS84_E2) + height) * sin_lat
        return x, y, z

    @staticmethod
    def _ecef_to_wgs84(x, y, z):
        b = WGS84_A * (1.0 - WGS84_F)
        ep2 = (WGS84_A * WGS84_A - b * b) / (b * b)
        p = math.hypot(x, y)
        theta = math.atan2(z * WGS84_A, p * b)
        lon = math.atan2(y, x)
        lat = math.atan2(
            z + ep2 * b * math.sin(theta) ** 3,
            p - WGS84_E2 * WGS84_A * math.cos(theta) ** 3,
        )
        n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * math.sin(lat) ** 2)
        height = p / math.cos(lat) - n
        return math.degrees(lon), math.degrees(lat), height

    @staticmethod
    def _wgs84_to_utm(lon, lat, zone, hemisphere):
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        lon0 = math.radians((zone - 1) * 6 - 180 + 3)
        ep2 = WGS84_E2 / (1 - WGS84_E2)
        n = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(lat_rad) ** 2)
        t = math.tan(lat_rad) ** 2
        c = ep2 * math.cos(lat_rad) ** 2
        a = math.cos(lat_rad) * (lon_rad - lon0)
        m = WGS84_A * (
            (1 - WGS84_E2 / 4 - 3 * WGS84_E2 ** 2 / 64 - 5 * WGS84_E2 ** 3 / 256) * lat_rad
            - (3 * WGS84_E2 / 8 + 3 * WGS84_E2 ** 2 / 32 + 45 * WGS84_E2 ** 3 / 1024) * math.sin(2 * lat_rad)
            + (15 * WGS84_E2 ** 2 / 256 + 45 * WGS84_E2 ** 3 / 1024) * math.sin(4 * lat_rad)
            - (35 * WGS84_E2 ** 3 / 3072) * math.sin(6 * lat_rad)
        )
        easting = UTM_K0 * n * (a + (1 - t + c) * a ** 3 / 6 + (5 - 18 * t + t ** 2 + 72 * c - 58 * ep2) * a ** 5 / 120) + 500000
        northing = UTM_K0 * (
            m + n * math.tan(lat_rad) * (
                a ** 2 / 2 + (5 - t + 9 * c + 4 * c ** 2) * a ** 4 / 24
                + (61 - 58 * t + t ** 2 + 600 * c - 330 * ep2) * a ** 6 / 720
            )
        )
        if hemisphere == "S":
            northing += 10000000
        return easting, northing

    @staticmethod
    def _utm_to_wgs84(easting, northing, zone, hemisphere, height=0.0):
        x = easting - 500000.0
        y = northing - (10000000.0 if hemisphere == "S" else 0.0)
        lon0 = math.radians((zone - 1) * 6 - 180 + 3)
        ep2 = WGS84_E2 / (1 - WGS84_E2)
        m = y / UTM_K0
        mu = m / (WGS84_A * (1 - WGS84_E2 / 4 - 3 * WGS84_E2 ** 2 / 64 - 5 * WGS84_E2 ** 3 / 256))
        e1 = (1 - math.sqrt(1 - WGS84_E2)) / (1 + math.sqrt(1 - WGS84_E2))
        j1 = 3 * e1 / 2 - 27 * e1 ** 3 / 32
        j2 = 21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32
        j3 = 151 * e1 ** 3 / 96
        j4 = 1097 * e1 ** 4 / 512
        fp = mu + j1 * math.sin(2 * mu) + j2 * math.sin(4 * mu) + j3 * math.sin(6 * mu) + j4 * math.sin(8 * mu)
        c1 = ep2 * math.cos(fp) ** 2
        t1 = math.tan(fp) ** 2
        n1 = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(fp) ** 2)
        r1 = WGS84_A * (1 - WGS84_E2) / (1 - WGS84_E2 * math.sin(fp) ** 2) ** 1.5
        d = x / (n1 * UTM_K0)
        lat = fp - (n1 * math.tan(fp) / r1) * (
            d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24
            + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2 - 3 * c1 ** 2) * d ** 6 / 720
        )
        lon = lon0 + (
            d - (1 + 2 * t1 + c1) * d ** 3 / 6
            + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2) * d ** 5 / 120
        ) / math.cos(fp)
        return math.degrees(lon), math.degrees(lat), height


class GISManager:
    """Workspace-owned GIS project and data management system."""

    def __init__(self):
        self.projects = []
        self.active_project_id = None
        self.coordinate_systems = CoordinateSystemManagerGIS()
        self.terrain_manager = TerrainManager(self)
        self.terrain = self.terrain_manager
        from engine.terrain_runtime import ProductionTerrainRuntime
        self.terrain_production_runtime = ProductionTerrainRuntime(self)
        self.production_runtime = self.terrain_production_runtime

    @property
    def active_project(self):
        if not self.projects:
            return None
        return self.get_project(self.active_project_id) or self.projects[-1]

    def create_project(self, name="GIS Project", default_crs="EPSG:4326", metadata=None):
        if not self.coordinate_systems.validate(default_crs):
            raise ValueError(f"Unsupported project CRS '{default_crs}'.")
        project = GISProject(name=name, metadata=dict(metadata or {}), default_crs=default_crs)
        project.workspace.project_id = project.id
        project.workspace.spatial_reference = self.coordinate_systems.get(default_crs).to_dict()
        self.add_project(project)
        return project

    def initialize(self, project_name="GIS Project", default_crs="EPSG:4326", metadata=None, preferences=None):
        project = self.active_project or self.create_project(project_name, default_crs, metadata)
        project.name = project_name or project.name
        project.default_crs = default_crs or project.default_crs
        project.metadata.update(dict(metadata or {}))
        project.workspace.active = True
        project.workspace.preferences.update(dict(preferences or {}))
        project.workspace.spatial_reference = self.coordinate_systems.get(project.default_crs).to_dict()
        self.active_project_id = project.id
        self.refresh_diagnostics(project)
        return project.workspace

    def add_project(self, project):
        if project not in self.projects:
            self.projects.append(project)
        self.active_project_id = project.id
        self.refresh_diagnostics(project)
        return project

    def get_project(self, project):
        if isinstance(project, GISProject):
            return project if project in self.projects else None
        for item in self.projects:
            if item.id == project or item.name == project:
                return item
        return None

    def ensure_project(self):
        return self.active_project or self.create_project()

    def add_layer(self, layer):
        project = self.ensure_project()
        if layer not in project.layers:
            project.layers.append(layer)
        self.refresh_indexes(project)
        self.refresh_diagnostics(project)
        return layer

    def remove_layer(self, layer):
        project = self.active_project
        if project and layer in project.layers:
            project.layers.remove(layer)
            self.refresh_indexes(project)
            self.refresh_diagnostics(project)
            return True
        return False

    def create_survey_point(self, name, x, y, z=0.0, crs=None, point_type="Survey Point", elevation=None, metadata=None):
        project = self.ensure_project()
        coordinate = GISCoordinate(float(x), float(y), float(z), crs or project.default_crs)
        point = SurveyPoint(name, coordinate, point_type, float(elevation if elevation is not None else z), dict(metadata or {}))
        project.survey_points.append(point)
        self.refresh_indexes(project)
        self.refresh_diagnostics(project)
        return point

    def remove_survey_point(self, point):
        project = self.active_project
        if project and point in project.survey_points:
            project.survey_points.remove(point)
            self.refresh_indexes(project)
            self.refresh_diagnostics(project)
            return True
        return False

    def import_file(self, file_path, layer_name=None, target_crs=None, source_crs=None, import_as_survey=False):
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(str(path))
        suffix = path.suffix.lower()
        if suffix == ".geojson" or suffix == ".json":
            layer, record = self._import_geojson(path, layer_name, source_crs)
        elif suffix == ".shp":
            layer, record = self._import_shapefile(path, layer_name, source_crs)
        elif suffix == ".kml":
            layer, record = self._import_kml(path, layer_name, source_crs)
        elif suffix == ".kmz":
            layer, record = self._import_kmz(path, layer_name, source_crs)
        elif suffix == ".gpx":
            layer, record = self._import_gpx(path, layer_name, source_crs)
        elif suffix == ".csv":
            layer, record = self._import_csv(path, layer_name, source_crs)
        else:
            raise ValueError(f"Unsupported GIS import format '{suffix}'.")
        if target_crs and target_crs != layer.crs:
            layer.features = [
                GISFeature(
                    feature.geometry_type,
                    self.coordinate_systems.project_coordinates(feature.coordinates, feature.crs, target_crs),
                    feature.attributes,
                    target_crs,
                    feature.feature_class,
                    feature.metadata,
                    feature.id,
                )
                for feature in layer.features
            ]
            layer.crs = target_crs
            record.crs = target_crs
        self.add_layer(layer)
        record.layer_ids.append(layer.id)
        self.ensure_project().import_records.append(record)
        if import_as_survey:
            for feature in layer.features:
                if feature.geometry_type == "Point" and feature.coordinates:
                    coordinate = feature.coordinates[0]
                    self.create_survey_point(
                        str(feature.attributes.get("name") or feature.attributes.get("id") or f"Survey {len(self.ensure_project().survey_points) + 1}"),
                        coordinate[0],
                        coordinate[1],
                        coordinate[2] if len(coordinate) > 2 else 0.0,
                        layer.crs,
                        "Survey Point",
                        coordinate[2] if len(coordinate) > 2 else 0.0,
                        feature.attributes,
                    )
        self.validate_import(record)
        self.refresh_diagnostics(self.ensure_project())
        return record

    def validate_crs(self, code):
        issues = [] if self.coordinate_systems.validate(code) else [f"Unsupported CRS '{code}'."]
        return GISValidationReport(not issues, issues, [], {"crs": code})

    def validate_coordinates(self, coordinates, crs="EPSG:4326"):
        issues = []
        definition = self.coordinate_systems.get(crs)
        if definition is None:
            issues.append(f"Unsupported CRS '{crs}'.")
        for point in _deep_coordinates(coordinates):
            if len(point) < 2:
                issues.append("Coordinate must contain at least x/y or lon/lat.")
                continue
            if definition and definition.crs_type == "geographic":
                if not -180.0 <= point[0] <= 180.0:
                    issues.append(f"Longitude out of range: {point[0]}.")
                if not -90.0 <= point[1] <= 90.0:
                    issues.append(f"Latitude out of range: {point[1]}.")
        return GISValidationReport(not issues, issues, [], {"points": len(_deep_coordinates(coordinates)), "crs": crs})

    def validate_import(self, record):
        issues = list(record.errors)
        warnings = list(record.warnings)
        for layer_id in record.layer_ids:
            layer = self.get_layer(layer_id)
            if layer is None:
                issues.append(f"Import record references missing layer '{layer_id}'.")
            else:
                layer_report = self.validate_layer(layer)
                issues.extend(layer_report.issues)
                warnings.extend(layer_report.warnings)
        report = GISValidationReport(not issues, issues, warnings, {"feature_count": record.feature_count, "format": record.format_name})
        record.metadata["validation"] = report.to_dict()
        return report

    def validate_layer(self, layer):
        issues = []
        warnings = []
        if not layer.name:
            issues.append("GIS layer requires a name.")
        if not self.coordinate_systems.validate(layer.crs):
            issues.append(f"GIS layer '{layer.name}' uses unsupported CRS '{layer.crs}'.")
        for feature in layer.features:
            if not feature.geometry_type:
                issues.append(f"Layer '{layer.name}' contains a feature without geometry type.")
            coord_report = self.validate_coordinates(feature.coordinates, feature.crs)
            issues.extend(coord_report.issues)
            if not feature.attributes:
                warnings.append(f"Feature '{feature.id}' in layer '{layer.name}' has no attributes.")
        return GISValidationReport(not issues, issues, warnings, {"features": len(layer.features)})

    def validate_survey(self):
        project = self.ensure_project()
        issues = []
        names = set()
        for point in project.survey_points:
            if point.name in names:
                issues.append(f"Duplicate survey point name '{point.name}'.")
            names.add(point.name)
            issues.extend(self.validate_coordinates([[point.coordinate.x, point.coordinate.y, point.coordinate.z]], point.coordinate.crs).issues)
        return GISValidationReport(not issues, issues, [], {"survey_points": len(project.survey_points)})

    def validate_project(self):
        project = self.ensure_project()
        issues = []
        warnings = []
        if not project.workspace.active:
            issues.append("GIS Workspace is not active.")
        issues.extend(self.validate_crs(project.default_crs).issues)
        layer_names = set()
        for layer in project.layers:
            if layer.name in layer_names:
                issues.append(f"Duplicate GIS layer name '{layer.name}'.")
            layer_names.add(layer.name)
            report = self.validate_layer(layer)
            issues.extend(report.issues)
            warnings.extend(report.warnings)
        survey = self.validate_survey()
        issues.extend(survey.issues)
        diagnostics = self.refresh_diagnostics(project).to_dict()
        report = GISValidationReport(not issues, issues, warnings, diagnostics)
        project.validation_report = report
        return report

    def refresh_indexes(self, project=None):
        project = project or self.ensure_project()
        feature_index = {}
        attribute_index = {}
        spatial_index = {}
        for layer in project.layers:
            spatial_index[layer.id] = []
            for feature in layer.features:
                feature_index[feature.id] = layer.id
                for key, value in feature.attributes.items():
                    attribute_index.setdefault(str(key), {}).setdefault(str(value), []).append(feature.id)
                bounds = feature.bounds()
                if bounds:
                    spatial_index[layer.id].append({"feature_id": feature.id, "bounds": bounds})
        project.indexes = {
            "features": feature_index,
            "attributes": attribute_index,
            "spatial": spatial_index,
            "layers": {layer.id: layer.name for layer in project.layers},
            "metadata": {"updated_at": _utc_timestamp()},
        }
        return project.indexes

    def visualization_metadata(self):
        project = self.ensure_project()
        project.visualization_metadata = {
            "gis_layers": {
                layer.id: {
                    "name": layer.name,
                    "visible": layer.visible,
                    "locked": layer.locked,
                    "group": layer.group,
                    "feature_count": len(layer.features),
                    "bounds": self._layer_bounds(layer),
                }
                for layer in project.layers
            },
            "survey_points": {point.id: point.to_dict() for point in project.survey_points},
            "coordinate_grids": {"project_crs": project.default_crs, "local_origin": project.local_origin.to_dict()},
            "reference_systems": {project.default_crs: self.coordinate_systems.get(project.default_crs).to_dict()},
            "feature_previews": {
                feature.id: {
                    "layer_id": layer.id,
                    "geometry_type": feature.geometry_type,
                    "bounds": feature.bounds(),
                    "attribute_keys": sorted(feature.attributes),
                }
                for layer in project.layers for feature in layer.features
            },
            "selection": {},
            "diagnostics": project.diagnostics.to_dict(),
        }
        return project.visualization_metadata

    def diagnostics_report(self):
        return self.refresh_diagnostics(self.ensure_project())

    def refresh_diagnostics(self, project=None):
        project = project or self.ensure_project()
        diagnostics = GISDiagnostics(
            len(self.projects),
            len(project.layers),
            sum(len(layer.features) for layer in project.layers),
            len(project.survey_points),
            len(project.import_records),
            len(self.coordinate_systems.registry),
            len(getattr(project.validation_report, "issues", [])),
        )
        project.diagnostics = diagnostics
        return diagnostics

    def get_layer(self, layer):
        project = self.active_project
        if project is None:
            return None
        if isinstance(layer, GISLayer):
            return layer if layer in project.layers else None
        for item in project.layers:
            if item.id == layer or item.name == layer:
                return item
        return None

    def visible_objects(self):
        project = self.active_project
        return [] if project is None else [layer for layer in project.layers if layer.visible]

    def clear(self):
        self.projects.clear()
        self.active_project_id = None
        self.terrain_manager.clear()
        self.terrain_production_runtime.clear()

    def to_dict(self):
        return {
            "active_project_id": self.active_project_id,
            "coordinate_systems": self.coordinate_systems.to_dict(),
            "projects": [project.to_dict() for project in self.projects],
            "terrain": self.terrain_manager.to_dict(),
            "production_runtime": self.terrain_production_runtime.to_dict(),
        }

    def from_dict(self, data):
        data = data or {}
        self.coordinate_systems.from_dict(data.get("coordinate_systems", {}))
        self.projects = [GISProject.from_dict(item) for item in data.get("projects", [])]
        self.active_project_id = data.get("active_project_id")
        if self.projects and not self.active_project_id:
            self.active_project_id = self.projects[-1].id
        self.terrain_manager.from_dict(data.get("terrain", {}))
        self.terrain_production_runtime.from_dict(data.get("production_runtime", {}))

    def _import_geojson(self, path, layer_name=None, source_crs=None):
        data = json.loads(path.read_text(encoding="utf-8"))
        crs = source_crs or self._geojson_crs(data) or "EPSG:4326"
        features = []
        if data.get("type") == "FeatureCollection":
            iterable = data.get("features", [])
        elif data.get("type") == "Feature":
            iterable = [data]
        else:
            iterable = [{"type": "Feature", "geometry": data, "properties": {}}]
        for item in iterable:
            geometry = item.get("geometry") or {}
            if not geometry:
                continue
            features.append(GISFeature(
                geometry.get("type", ""),
                geometry.get("coordinates", []),
                dict(item.get("properties", {})),
                crs,
                item.get("id", "") or geometry.get("type", ""),
                {"source_format": "GeoJSON"},
            ))
        layer = GISLayer(layer_name or path.stem, "Vector", crs, features, metadata={"source_path": str(path), "format": "GeoJSON"})
        return layer, GISImportRecord(str(path), "GeoJSON", feature_count=len(features), crs=crs)

    def _import_kml(self, path, layer_name=None, source_crs=None):
        return self._layer_from_kml_text(path.read_text(encoding="utf-8"), layer_name or path.stem, str(path), "KML", source_crs)

    def _import_kmz(self, path, layer_name=None, source_crs=None):
        with zipfile.ZipFile(path, "r") as archive:
            names = [name for name in archive.namelist() if name.lower().endswith(".kml")]
            if not names:
                raise ValueError("KMZ archive contains no KML document.")
            text = archive.read(names[0]).decode("utf-8")
        return self._layer_from_kml_text(text, layer_name or path.stem, str(path), "KMZ", source_crs)

    def _import_gpx(self, path, layer_name=None, source_crs=None):
        root = ElementTree.parse(path).getroot()
        crs = source_crs or "EPSG:4326"
        features = []
        for point in root.findall(".//{*}wpt"):
            features.append(GISFeature("Point", [[_as_float(point.get("lon")), _as_float(point.get("lat")), _as_float(_xml_text(point, "ele"))]], {"name": _xml_text(point, "name")}, crs, "Waypoint", {"source_format": "GPX"}))
        for route in root.findall(".//{*}rte"):
            coords = [[_as_float(pt.get("lon")), _as_float(pt.get("lat")), _as_float(_xml_text(pt, "ele"))] for pt in route.findall("{*}rtept")]
            if coords:
                features.append(GISFeature("LineString", coords, {"name": _xml_text(route, "name")}, crs, "Route", {"source_format": "GPX"}))
        for track in root.findall(".//{*}trk"):
            for segment in track.findall(".//{*}trkseg"):
                coords = [[_as_float(pt.get("lon")), _as_float(pt.get("lat")), _as_float(_xml_text(pt, "ele"))] for pt in segment.findall("{*}trkpt")]
                if coords:
                    features.append(GISFeature("LineString", coords, {"name": _xml_text(track, "name")}, crs, "Track", {"source_format": "GPX"}))
        layer = GISLayer(layer_name or path.stem, "Vector", crs, features, metadata={"source_path": str(path), "format": "GPX"})
        return layer, GISImportRecord(str(path), "GPX", feature_count=len(features), crs=crs)

    def _import_csv(self, path, layer_name=None, source_crs=None):
        crs = source_crs or "EPSG:4326"
        features = []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError("CSV coordinate import requires a header row.")
            lower = {name.lower(): name for name in reader.fieldnames}
            x_key = lower.get("lon") or lower.get("longitude") or lower.get("x") or lower.get("easting")
            y_key = lower.get("lat") or lower.get("latitude") or lower.get("y") or lower.get("northing")
            z_key = lower.get("z") or lower.get("elevation") or lower.get("height")
            if not x_key or not y_key:
                raise ValueError("CSV coordinate import requires longitude/latitude, x/y or easting/northing columns.")
            for row in reader:
                attrs = dict(row)
                features.append(GISFeature("Point", [[_as_float(row.get(x_key)), _as_float(row.get(y_key)), _as_float(row.get(z_key))]], attrs, crs, "CSV Point", {"source_format": "CSV"}))
        layer = GISLayer(layer_name or path.stem, "Vector", crs, features, metadata={"source_path": str(path), "format": "CSV"})
        return layer, GISImportRecord(str(path), "CSV", feature_count=len(features), crs=crs)

    def _import_shapefile(self, path, layer_name=None, source_crs=None):
        crs = source_crs or self._prj_crs(path.with_suffix(".prj")) or "EPSG:4326"
        shapes = self._read_shp(path)
        attributes = self._read_dbf(path.with_suffix(".dbf")) if path.with_suffix(".dbf").exists() else [{} for _ in shapes]
        features = []
        for index, shape in enumerate(shapes):
            attrs = attributes[index] if index < len(attributes) else {}
            features.append(GISFeature(shape["geometry_type"], shape["coordinates"], attrs, crs, shape["geometry_type"], {"source_format": "Shapefile", "shape_type": shape["shape_type"]}))
        layer = GISLayer(layer_name or path.stem, "Vector", crs, features, metadata={"source_path": str(path), "format": "ESRI Shapefile"})
        return layer, GISImportRecord(str(path), "ESRI Shapefile", feature_count=len(features), crs=crs)

    def _layer_from_kml_text(self, text, layer_name, source_path, format_name, source_crs=None):
        root = ElementTree.fromstring(text)
        crs = source_crs or "EPSG:4326"
        features = []
        for placemark in root.findall(".//{*}Placemark"):
            attrs = {"name": _xml_text(placemark, "name"), "description": _xml_text(placemark, "description")}
            point = placemark.find(".//{*}Point/{*}coordinates")
            line = placemark.find(".//{*}LineString/{*}coordinates")
            polygon = placemark.find(".//{*}Polygon//{*}outerBoundaryIs/{*}LinearRing/{*}coordinates")
            if point is not None and point.text:
                features.append(GISFeature("Point", [_parse_kml_coordinate(point.text.strip())], attrs, crs, "Placemark", {"source_format": format_name}))
            if line is not None and line.text:
                features.append(GISFeature("LineString", _parse_kml_coordinates(line.text), attrs, crs, "Placemark", {"source_format": format_name}))
            if polygon is not None and polygon.text:
                features.append(GISFeature("Polygon", [_parse_kml_coordinates(polygon.text)], attrs, crs, "Placemark", {"source_format": format_name}))
        layer = GISLayer(layer_name, "Vector", crs, features, metadata={"source_path": source_path, "format": format_name})
        return layer, GISImportRecord(source_path, format_name, feature_count=len(features), crs=crs)

    @staticmethod
    def _geojson_crs(data):
        crs = data.get("crs") if isinstance(data, dict) else None
        if isinstance(crs, dict):
            name = crs.get("properties", {}).get("name")
            if name and "EPSG" in name.upper():
                parts = name.upper().replace("URN:OGC:DEF:CRS:", "").replace("::", ":").split(":")
                if parts[-2].isdigit():
                    return f"EPSG:{parts[-2]}"
                if parts[-1].isdigit():
                    return f"EPSG:{parts[-1]}"
        return None

    @staticmethod
    def _prj_crs(path):
        if not path.exists():
            return None
        text = path.read_text(errors="ignore").upper()
        if "WGS_1984_UTM_ZONE" in text or "WGS 84 / UTM ZONE" in text:
            digits = "".join(ch for ch in text.split("UTM_ZONE", 1)[-1][:4] if ch.isdigit())
            if digits:
                zone = int(digits[:2])
                return f"EPSG:{32600 + zone}"
        if "WGS_1984" in text or "WGS 84" in text:
            return "EPSG:4326"
        return None

    @staticmethod
    def _read_shp(path):
        data = path.read_bytes()
        if len(data) < 100:
            raise ValueError("Invalid shapefile: header is shorter than 100 bytes.")
        if struct.unpack(">i", data[:4])[0] != 9994:
            raise ValueError("Invalid shapefile file code.")
        offset = 100
        shapes = []
        while offset + 8 <= len(data):
            record_number, content_length_words = struct.unpack(">2i", data[offset:offset + 8])
            offset += 8
            content_length = content_length_words * 2
            content = data[offset:offset + content_length]
            offset += content_length
            if len(content) < 4:
                continue
            shape_type = struct.unpack("<i", content[:4])[0]
            if shape_type == 0:
                continue
            if shape_type in (1, 11, 21):
                x, y = struct.unpack("<2d", content[4:20])
                shapes.append({"shape_type": shape_type, "geometry_type": "Point", "coordinates": [[x, y]]})
            elif shape_type in (3, 5, 13, 15, 23, 25):
                if len(content) < 44:
                    raise ValueError(f"Invalid shapefile record {record_number}.")
                num_parts, num_points = struct.unpack("<2i", content[36:44])
                parts_offset = 44
                parts = list(struct.unpack(f"<{num_parts}i", content[parts_offset:parts_offset + 4 * num_parts]))
                points_offset = parts_offset + 4 * num_parts
                points = [list(struct.unpack("<2d", content[points_offset + i * 16:points_offset + i * 16 + 16])) for i in range(num_points)]
                parts.append(num_points)
                rings = [points[parts[i]:parts[i + 1]] for i in range(num_parts)]
                if shape_type in (3, 13, 23):
                    coords = rings[0] if len(rings) == 1 else rings
                    geom_type = "LineString" if len(rings) == 1 else "MultiLineString"
                else:
                    coords = rings
                    geom_type = "Polygon"
                shapes.append({"shape_type": shape_type, "geometry_type": geom_type, "coordinates": coords})
            elif shape_type in (8, 18, 28):
                num_points = struct.unpack("<i", content[36:40])[0]
                points = [list(struct.unpack("<2d", content[40 + i * 16:40 + i * 16 + 16])) for i in range(num_points)]
                shapes.append({"shape_type": shape_type, "geometry_type": "MultiPoint", "coordinates": points})
            else:
                raise ValueError(f"Unsupported shapefile shape type {shape_type}.")
        return shapes

    @staticmethod
    def _read_dbf(path):
        data = path.read_bytes()
        if len(data) < 32:
            return []
        record_count = struct.unpack("<I", data[4:8])[0]
        header_length = struct.unpack("<H", data[8:10])[0]
        record_length = struct.unpack("<H", data[10:12])[0]
        fields = []
        offset = 32
        while offset + 32 <= header_length and data[offset] != 0x0D:
            raw_name = data[offset:offset + 11].split(b"\x00", 1)[0].decode("ascii", errors="ignore").strip()
            field_type = chr(data[offset + 11])
            length = data[offset + 16]
            decimal = data[offset + 17]
            fields.append((raw_name, field_type, length, decimal))
            offset += 32
        records = []
        offset = header_length
        for _ in range(record_count):
            record = data[offset:offset + record_length]
            offset += record_length
            if not record or record[0:1] == b"*":
                continue
            attrs = {}
            pos = 1
            for name, field_type, length, decimal in fields:
                raw = record[pos:pos + length].decode("utf-8", errors="ignore").strip()
                pos += length
                if field_type in ("N", "F") and raw:
                    attrs[name] = float(raw) if decimal else int(float(raw))
                elif field_type == "L":
                    attrs[name] = raw.upper() in ("Y", "T", "1")
                else:
                    attrs[name] = raw
            records.append(attrs)
        return records

    @staticmethod
    def _layer_bounds(layer):
        bounds = [feature.bounds() for feature in layer.features if feature.bounds()]
        if not bounds:
            return None
        return [min(item[0] for item in bounds), min(item[1] for item in bounds), max(item[2] for item in bounds), max(item[3] for item in bounds)]


def _parse_kml_coordinate(text):
    parts = [part for part in text.replace("\n", " ").split(",") if part != ""]
    values = [_as_float(part) for part in parts[:3]]
    while len(values) < 3:
        values.append(0.0)
    return values


def _parse_kml_coordinates(text):
    return [_parse_kml_coordinate(item) for item in text.replace("\n", " ").split() if item.strip()]


def _xml_text(node, local_name):
    child = node.find(f".//{{*}}{local_name}")
    return child.text.strip() if child is not None and child.text else ""

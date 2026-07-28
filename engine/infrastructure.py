import json
import math
import sqlite3
import struct
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree

from engine.gis import GISFeature, GISLayer


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
class InfrastructureSettings:
    """Reusable infrastructure settings."""

    default_crs: str = "EPSG:4326"
    station_interval: float = 10.0
    road_design_speed: float = 50.0
    utility_clearance: float = 1.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "default_crs": self.default_crs,
            "station_interval": self.station_interval,
            "road_design_speed": self.road_design_speed,
            "utility_clearance": self.utility_clearance,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return InfrastructureSettings(
            data.get("default_crs", "EPSG:4326"),
            _f(data.get("station_interval"), 10.0),
            _f(data.get("road_design_speed"), 50.0),
            _f(data.get("utility_clearance"), 1.0),
            dict(data.get("metadata", {})),
        )


@dataclass
class InfrastructureValidationReport:
    """Infrastructure validation report."""

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
        return InfrastructureValidationReport(
            bool(data.get("valid", True)),
            list(data.get("issues", [])),
            list(data.get("warnings", [])),
            dict(data.get("statistics", {})),
            data.get("generated_at", _timestamp()),
        )


@dataclass
class InfrastructureDiagnostics:
    """Infrastructure diagnostics summary."""

    projects: int = 0
    roads: int = 0
    parcels: int = 0
    utility_networks: int = 0
    utility_nodes: int = 0
    utility_edges: int = 0
    alignments: int = 0
    imports: int = 0
    synchronized_layers: int = 0
    validation_issues: int = 0
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        data = data or {}
        return InfrastructureDiagnostics(
            int(data.get("projects", 0)),
            int(data.get("roads", 0)),
            int(data.get("parcels", 0)),
            int(data.get("utility_networks", 0)),
            int(data.get("utility_nodes", 0)),
            int(data.get("utility_edges", 0)),
            int(data.get("alignments", 0)),
            int(data.get("imports", 0)),
            int(data.get("synchronized_layers", 0)),
            int(data.get("validation_issues", 0)),
            data.get("updated_at", _timestamp()),
        )


@dataclass
class InfrastructureProject:
    """Civil infrastructure project metadata scoped to site engineering."""

    name: str = "Infrastructure Project"
    settings: InfrastructureSettings = field(default_factory=InfrastructureSettings)
    metadata: dict = field(default_factory=dict)
    roads: list = field(default_factory=list)
    parcels: list = field(default_factory=list)
    utility_networks: list = field(default_factory=list)
    alignments: list = field(default_factory=list)
    imports: list = field(default_factory=list)
    synchronized_layers: list = field(default_factory=list)
    indexes: dict = field(default_factory=dict)
    visualization_metadata: dict = field(default_factory=dict)
    validation_report: InfrastructureValidationReport = field(default_factory=InfrastructureValidationReport)
    diagnostics: InfrastructureDiagnostics = field(default_factory=InfrastructureDiagnostics)
    id: str = field(default_factory=lambda: str(uuid4()))
    version_metadata: dict = field(default_factory=lambda: {"release": "2.0", "batch": "D"})

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "settings": self.settings.to_dict(),
            "metadata": dict(self.metadata),
            "roads": [dict(item) for item in self.roads],
            "parcels": [dict(item) for item in self.parcels],
            "utility_networks": [dict(item) for item in self.utility_networks],
            "alignments": [dict(item) for item in self.alignments],
            "imports": [dict(item) for item in self.imports],
            "synchronized_layers": [dict(item) for item in self.synchronized_layers],
            "indexes": dict(self.indexes),
            "visualization_metadata": dict(self.visualization_metadata),
            "validation_report": self.validation_report.to_dict(),
            "diagnostics": self.diagnostics.to_dict(),
            "version_metadata": dict(self.version_metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return InfrastructureProject(
            data.get("name", "Infrastructure Project"),
            InfrastructureSettings.from_dict(data.get("settings", {})),
            dict(data.get("metadata", {})),
            [dict(item) for item in data.get("roads", [])],
            [dict(item) for item in data.get("parcels", [])],
            [dict(item) for item in data.get("utility_networks", [])],
            [dict(item) for item in data.get("alignments", [])],
            [dict(item) for item in data.get("imports", [])],
            [dict(item) for item in data.get("synchronized_layers", [])],
            dict(data.get("indexes", {})),
            dict(data.get("visualization_metadata", {})),
            InfrastructureValidationReport.from_dict(data.get("validation_report", {})),
            InfrastructureDiagnostics.from_dict(data.get("diagnostics", {})),
            data.get("id", str(uuid4())),
            dict(data.get("version_metadata", {"release": "2.0", "batch": "D"})),
        )


class InfrastructureManager:
    """Site-scoped infrastructure manager; owns infrastructure metadata and GIS records only."""

    def __init__(self, site_engineering_manager=None):
        self.site_engineering_manager = site_engineering_manager
        self.projects = []
        self.active_project_id = None
        from engine.ai_site_intelligence import AISiteIntelligenceManager
        self.ai_site_intelligence_manager = AISiteIntelligenceManager(self)
        self.ai_site_intelligence = self.ai_site_intelligence_manager

    @property
    def active_project(self):
        if not self.projects:
            return None
        return self.get_project(self.active_project_id) or self.projects[-1]

    def create_project(self, name="Infrastructure Project", settings=None, metadata=None):
        project = InfrastructureProject(name, settings if isinstance(settings, InfrastructureSettings) else InfrastructureSettings.from_dict(settings or {}), dict(metadata or {}))
        self.projects.append(project)
        self.active_project_id = project.id
        self.refresh_diagnostics(project)
        return project

    def ensure_project(self):
        return self.active_project or self.create_project()

    def get_project(self, project):
        if isinstance(project, InfrastructureProject):
            return project if project in self.projects else None
        return next((item for item in self.projects if item.id == project or item.name == project), None)

    def add_road(self, name, centerline, horizontal_alignment=None, vertical_alignment=None, lanes=None, hierarchy="Local", metadata=None):
        if len(centerline or []) < 2:
            raise ValueError("Road centerline requires at least two points.")
        road = {
            "id": str(uuid4()),
            "name": name,
            "centerline": [list(map(float, point[:2])) for point in centerline],
            "horizontal_alignment": horizontal_alignment or _alignment_from_polyline(centerline),
            "vertical_alignment": vertical_alignment or _vertical_alignment(centerline),
            "corridor": _road_corridor(centerline, lanes or [{"name": "Lane 1", "width": 3.5}, {"name": "Lane 2", "width": 3.5}]),
            "lanes": [dict(item) for item in lanes or [{"name": "Lane 1", "width": 3.5}, {"name": "Lane 2", "width": 3.5}]],
            "hierarchy": hierarchy,
            "intersections": [],
            "metadata": dict(metadata or {}),
            "validation": {"valid": True},
            "created_at": _timestamp(),
        }
        project = self.ensure_project()
        for other in project.roads:
            hits = _polyline_intersections(road["centerline"], other["centerline"])
            if hits:
                road["intersections"].extend([{"road_id": other["id"], "point": hit} for hit in hits])
                other.setdefault("intersections", []).extend([{"road_id": road["id"], "point": hit} for hit in hits])
        project.roads.append(road)
        self.rebuild_indexes(project)
        self.refresh_diagnostics(project)
        return road

    def update_road(self, road_ref, **updates):
        road = self.road_for(road_ref)
        before = dict(road)
        if "centerline" in updates:
            centerline = updates["centerline"]
            if len(centerline or []) < 2:
                raise ValueError("Road centerline requires at least two points.")
            road["centerline"] = [list(map(float, point[:2])) for point in centerline]
            road["horizontal_alignment"] = _alignment_from_polyline(centerline)
            road["vertical_alignment"] = _vertical_alignment(centerline)
            road["corridor"] = _road_corridor(centerline, road.get("lanes", []))
        for key in ("lanes", "hierarchy", "metadata"):
            if key in updates:
                road[key] = updates[key]
        self.rebuild_indexes()
        self.refresh_diagnostics()
        return before, road

    def add_parcel(self, name, boundary, attributes=None, ownership=None, subdivision=None):
        if len(boundary or []) < 3:
            raise ValueError("Parcel boundary requires at least three points.")
        parcel = {
            "id": str(uuid4()),
            "name": name,
            "boundary": [list(map(float, point[:2])) for point in boundary],
            "area": _polygon_area(boundary),
            "centroid": _polygon_centroid(boundary),
            "attributes": dict(attributes or {}),
            "ownership_metadata": dict(ownership or {}),
            "subdivision_metadata": dict(subdivision or {}),
            "validation": {"valid": True},
            "created_at": _timestamp(),
        }
        self.ensure_project().parcels.append(parcel)
        self.rebuild_indexes()
        self.refresh_diagnostics()
        return parcel

    def add_utility_network(self, network_type, name, nodes=None, edges=None, corridor=None, metadata=None):
        nodes = [dict(item) for item in nodes or []]
        edges = [dict(item) for item in edges or []]
        node_ids = {node.get("id") for node in nodes}
        for edge in edges:
            if edge.get("from") not in node_ids or edge.get("to") not in node_ids:
                raise ValueError("Utility edge references missing network node.")
            a = next(node for node in nodes if node.get("id") == edge.get("from"))
            b = next(node for node in nodes if node.get("id") == edge.get("to"))
            edge["length"] = _distance2(a["point"], b["point"])
        network = {
            "id": str(uuid4()),
            "network_type": network_type,
            "name": name,
            "nodes": nodes,
            "edges": edges,
            "utility_corridor": corridor or _network_corridor(nodes),
            "metadata": dict(metadata or {}),
            "validation": {"valid": True},
            "created_at": _timestamp(),
        }
        self.ensure_project().utility_networks.append(network)
        self.rebuild_indexes()
        self.refresh_diagnostics()
        return network

    def add_alignment(self, name, polyline, alignment_type="Survey Alignment", metadata=None):
        if len(polyline or []) < 2:
            raise ValueError("Alignment requires at least two points.")
        alignment = {
            "id": str(uuid4()),
            "name": name,
            "alignment_type": alignment_type,
            "polyline": [list(map(float, point[:2])) for point in polyline],
            "stationing": _stationing(polyline, self.ensure_project().settings.station_interval),
            "chainage": _stationing(polyline, self.ensure_project().settings.station_interval),
            "control_lines": [list(map(float, point[:2])) for point in polyline],
            "reference_lines": _offset_reference_lines(polyline, 5.0),
            "metadata": dict(metadata or {}),
            "validation": {"valid": True},
            "created_at": _timestamp(),
        }
        self.ensure_project().alignments.append(alignment)
        self.rebuild_indexes()
        self.refresh_diagnostics()
        return alignment

    def import_osm(self, path):
        tree = ElementTree.parse(path)
        root = tree.getroot()
        nodes = {node.attrib["id"]: [float(node.attrib["lon"]), float(node.attrib["lat"])] for node in root.findall("node") if "lat" in node.attrib and "lon" in node.attrib}
        imported = {"roads": 0, "parcels": 0, "utilities": 0}
        for way in root.findall("way"):
            tags = {tag.attrib.get("k"): tag.attrib.get("v") for tag in way.findall("tag")}
            coords = [nodes[nd.attrib["ref"]] for nd in way.findall("nd") if nd.attrib.get("ref") in nodes]
            if len(coords) < 2:
                continue
            if "highway" in tags:
                self.add_road(tags.get("name", f"OSM Road {way.attrib.get('id')}"), coords, hierarchy=tags.get("highway", "road"), metadata={"osm_id": way.attrib.get("id"), "tags": tags})
                imported["roads"] += 1
            elif tags.get("landuse") or tags.get("parcel") or tags.get("boundary") == "cadastral":
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                self.add_parcel(tags.get("name", f"OSM Parcel {way.attrib.get('id')}"), coords, tags, {"source": "OpenStreetMap"}, {"osm_id": way.attrib.get("id")})
                imported["parcels"] += 1
            elif "utility" in tags or "pipeline" in tags or "power" in tags:
                net_nodes = [{"id": f"{way.attrib.get('id')}-{idx}", "point": coord} for idx, coord in enumerate(coords)]
                edges = [{"from": net_nodes[idx]["id"], "to": net_nodes[idx + 1]["id"]} for idx in range(len(net_nodes) - 1)]
                self.add_utility_network(tags.get("utility") or tags.get("pipeline") or tags.get("power"), tags.get("name", f"OSM Utility {way.attrib.get('id')}"), net_nodes, edges, metadata={"osm_id": way.attrib.get("id"), "tags": tags})
                imported["utilities"] += 1
        record = {"id": str(uuid4()), "format": "OpenStreetMap", "source_path": str(path), "counts": imported, "imported_at": _timestamp()}
        self.ensure_project().imports.append(record)
        self.refresh_diagnostics()
        return record

    def import_geopackage(self, path):
        conn = sqlite3.connect(path)
        try:
            rows = conn.execute("SELECT table_name, column_name, geometry_type_name, srs_id FROM gpkg_geometry_columns").fetchall()
            imported = []
            for table, geom_col, geom_type, srs_id in rows:
                columns = [row[1] for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]
                attr_columns = [col for col in columns if col != geom_col]
                for row in conn.execute(f'SELECT * FROM "{table}"').fetchall():
                    record = dict(zip(columns, row))
                    geometry = _decode_gpkg_geometry(record[geom_col])
                    attrs = {col: record[col] for col in attr_columns}
                    self._add_infrastructure_from_feature(table, geom_type, geometry, attrs, {"source": "GeoPackage", "srs_id": srs_id})
                    imported.append({"table": table, "geometry_type": geom_type, "attributes": attrs})
        finally:
            conn.close()
        record = {"id": str(uuid4()), "format": "GeoPackage", "source_path": str(path), "feature_count": len(imported), "features": imported, "imported_at": _timestamp()}
        self.ensure_project().imports.append(record)
        self.refresh_diagnostics()
        return record

    def synchronize_file(self, path, layer_name=None):
        gis = self._gis_manager()
        record = gis.import_file(path, layer_name=layer_name)
        layer_id = record.layer_ids[-1] if record.layer_ids else None
        layer = next((item for item in gis.ensure_project().layers if item.id == layer_id), None)
        synchronized = self.synchronize_layer(layer)
        synchronized["source_path"] = str(path)
        synchronized["format"] = layer.metadata.get("format", Path(path).suffix.lower())
        return synchronized

    def synchronize_layer(self, layer):
        if isinstance(layer, str):
            gis = self._gis_manager()
            layer = next((item for item in gis.ensure_project().layers if item.id == layer or item.name == layer), None)
        if layer is None:
            raise ValueError("GIS layer not found for infrastructure synchronization.")
        counts = {"roads": 0, "parcels": 0, "utilities": 0}
        for feature in layer.features:
            result = self._add_infrastructure_from_feature(layer.name, feature.geometry_type, feature.coordinates, feature.attributes, {"source_layer_id": layer.id, "crs": feature.crs})
            if result:
                counts[result] += 1
        record = {"id": str(uuid4()), "layer_id": layer.id, "layer_name": layer.name, "counts": counts, "synchronized_at": _timestamp()}
        self.ensure_project().synchronized_layers.append(record)
        self.refresh_diagnostics()
        return record

    def validate_project(self):
        project = self.ensure_project()
        issues, warnings = [], []
        road_names = set()
        for road in project.roads:
            if road["name"] in road_names:
                issues.append(f"Duplicate road name '{road['name']}'.")
            road_names.add(road["name"])
            if len(road.get("centerline", [])) < 2:
                issues.append(f"Road '{road['name']}' requires a centerline.")
        for parcel in project.parcels:
            if parcel.get("area", 0.0) <= 0.0:
                issues.append(f"Parcel '{parcel.get('name')}' has zero area.")
        for network in project.utility_networks:
            node_ids = {node.get("id") for node in network.get("nodes", [])}
            for edge in network.get("edges", []):
                if edge.get("from") not in node_ids or edge.get("to") not in node_ids:
                    issues.append(f"Utility network '{network.get('name')}' contains an invalid edge.")
        if not project.roads and not project.parcels and not project.utility_networks:
            warnings.append("Infrastructure project contains no modeled infrastructure objects.")
        project.validation_report = InfrastructureValidationReport(not issues, issues, warnings, self.refresh_diagnostics(project).to_dict())
        return project.validation_report

    def visualization_metadata(self):
        project = self.ensure_project()
        project.visualization_metadata = {
            "roads": {item["id"]: {"name": item["name"], "hierarchy": item["hierarchy"], "corridor": item["corridor"]} for item in project.roads},
            "parcels": {item["id"]: {"name": item["name"], "area": item["area"], "centroid": item["centroid"]} for item in project.parcels},
            "utilities": {item["id"]: {"type": item["network_type"], "nodes": len(item["nodes"]), "edges": len(item["edges"])} for item in project.utility_networks},
            "survey_alignments": {item["id"]: {"name": item["name"], "station_count": len(item["stationing"])} for item in project.alignments},
            "infrastructure_overlays": {"imports": len(project.imports), "synchronized_layers": len(project.synchronized_layers)},
            "selection": {},
            "diagnostics": project.diagnostics.to_dict(),
        }
        return project.visualization_metadata

    def rebuild_indexes(self, project=None):
        project = project or self.ensure_project()
        project.indexes = {
            "roads": {item["id"]: {"name": item["name"], "bounds": _bounds(item["centerline"])} for item in project.roads},
            "parcels": {item["id"]: {"name": item["name"], "area": item["area"], "bounds": _bounds(item["boundary"])} for item in project.parcels},
            "utilities": {item["id"]: {"name": item["name"], "type": item["network_type"], "nodes": len(item["nodes"]), "edges": len(item["edges"])} for item in project.utility_networks},
            "alignments": {item["id"]: {"name": item["name"], "length": item["stationing"][-1]["station"] if item["stationing"] else 0.0} for item in project.alignments},
            "updated_at": _timestamp(),
        }
        return project.indexes

    def refresh_diagnostics(self, project=None):
        project = project or self.ensure_project()
        project.diagnostics = InfrastructureDiagnostics(
            len(self.projects),
            len(project.roads),
            len(project.parcels),
            len(project.utility_networks),
            sum(len(item.get("nodes", [])) for item in project.utility_networks),
            sum(len(item.get("edges", [])) for item in project.utility_networks),
            len(project.alignments),
            len(project.imports),
            len(project.synchronized_layers),
            len(project.validation_report.issues),
        )
        return project.diagnostics

    def to_dict(self):
        return {
            "active_project_id": self.active_project_id,
            "projects": [project.to_dict() for project in self.projects],
            "ai_site_intelligence": self.ai_site_intelligence_manager.to_dict(),
        }

    def from_dict(self, data):
        data = data or {}
        self.projects = [InfrastructureProject.from_dict(item) for item in data.get("projects", [])]
        self.active_project_id = data.get("active_project_id") or (self.projects[-1].id if self.projects else None)
        self.ai_site_intelligence_manager.from_dict(data.get("ai_site_intelligence", {}))

    def clear(self):
        self.projects.clear()
        self.active_project_id = None
        self.ai_site_intelligence_manager.clear()

    def road_for(self, road_ref):
        project = self.ensure_project()
        road = next((item for item in project.roads if item["id"] == road_ref or item["name"] == road_ref or item is road_ref), None)
        if road is None:
            raise ValueError("Road not found.")
        return road

    def _gis_manager(self):
        site = self.site_engineering_manager
        terrain = getattr(site, "terrain_manager", None)
        gis = getattr(terrain, "gis_manager", None)
        if gis is None:
            raise ValueError("Infrastructure GIS synchronization requires the existing GIS Manager.")
        return gis

    def _add_infrastructure_from_feature(self, source, geometry_type, coordinates, attributes, metadata):
        attrs = dict(attributes or {})
        kind = _feature_kind(source, geometry_type, attrs)
        if kind == "roads":
            centerline = _first_line(coordinates)
            if len(centerline) >= 2:
                self.add_road(attrs.get("name", attrs.get("NAME", f"{source} Road")), centerline, hierarchy=attrs.get("highway", attrs.get("class", "GIS")), metadata={**metadata, "attributes": attrs})
                return "roads"
        if kind == "parcels":
            boundary = _first_polygon(coordinates)
            if len(boundary) >= 3:
                self.add_parcel(attrs.get("name", attrs.get("NAME", f"{source} Parcel")), boundary, attrs, {"source": source}, metadata)
                return "parcels"
        if kind == "utilities":
            line = _first_line(coordinates)
            if len(line) >= 2:
                nodes = [{"id": f"{source}-{str(uuid4())}", "point": point} for point in line]
                edges = [{"from": nodes[idx]["id"], "to": nodes[idx + 1]["id"]} for idx in range(len(nodes) - 1)]
                self.add_utility_network(attrs.get("utility", attrs.get("network", "Utility")), attrs.get("name", attrs.get("NAME", f"{source} Utility")), nodes, edges, metadata={**metadata, "attributes": attrs})
                return "utilities"
        return None


def _feature_kind(source, geometry_type, attrs):
    text = " ".join(str(value).lower() for value in [source, geometry_type, *attrs.keys(), *attrs.values()])
    if any(token in text for token in ("road", "street", "highway", "centerline")):
        return "roads"
    if any(token in text for token in ("parcel", "lot", "block", "cadastral", "property")):
        return "parcels"
    if any(token in text for token in ("water", "storm", "sanitary", "electrical", "telecom", "gas", "utility", "pipe", "power")):
        return "utilities"
    return "parcels" if "polygon" in geometry_type.lower() else "roads"


def _alignment_from_polyline(polyline):
    return {"segments": [{"start": list(a[:2]), "end": list(b[:2]), "length": _distance2(a, b), "bearing": _bearing(a, b)} for a, b in zip(polyline, polyline[1:])], "length": _polyline_length(polyline)}


def _vertical_alignment(polyline):
    stations = []
    total = 0.0
    previous = None
    for point in polyline:
        if previous is not None:
            total += _distance2(previous, point)
        stations.append({"station": total, "elevation": _f(point[2]) if len(point) > 2 else 0.0})
        previous = point
    return stations


def _road_corridor(centerline, lanes):
    width = sum(_f(lane.get("width"), 0.0) for lane in lanes)
    return {"centerline": [list(point[:2]) for point in centerline], "width": width, "area": width * _polyline_length(centerline)}


def _network_corridor(nodes):
    points = [node["point"] for node in nodes]
    return {"bounds": _bounds(points), "node_count": len(nodes)}


def _stationing(polyline, interval):
    length = _polyline_length(polyline)
    count = max(1, int(math.ceil(length / max(interval, 1e-9))))
    return [{"station": length * idx / count, "point": _point_at_station(polyline, length * idx / count)} for idx in range(count + 1)]


def _point_at_station(polyline, station):
    remaining = station
    for a, b in zip(polyline, polyline[1:]):
        segment = _distance2(a, b)
        if remaining <= segment or segment <= 1e-12:
            t = remaining / max(segment, 1e-12)
            return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
        remaining -= segment
    return list(polyline[-1][:2])


def _offset_reference_lines(polyline, offset):
    def offset_line(sign):
        result = []
        for idx, point in enumerate(polyline):
            a = polyline[max(0, idx - 1)]
            b = polyline[min(len(polyline) - 1, idx + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = max(math.hypot(dx, dy), 1e-12)
            result.append([point[0] - sign * dy / length * offset, point[1] + sign * dx / length * offset])
        return result
    return {"left": offset_line(1), "right": offset_line(-1)}


def _polyline_length(polyline):
    return sum(_distance2(a, b) for a, b in zip(polyline, polyline[1:]))


def _distance2(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _bearing(a, b):
    return (math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) + 360.0) % 360.0


def _bounds(points):
    if not points:
        return None
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def _polygon_area(polygon):
    total = 0.0
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        total += a[0] * b[1] - b[0] * a[1]
    return abs(total) * 0.5


def _polygon_centroid(polygon):
    area_twice = 0.0
    cx = cy = 0.0
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        cross = a[0] * b[1] - b[0] * a[1]
        area_twice += cross
        cx += (a[0] + b[0]) * cross
        cy += (a[1] + b[1]) * cross
    if abs(area_twice) <= 1e-12:
        return [sum(p[0] for p in polygon) / len(polygon), sum(p[1] for p in polygon) / len(polygon)]
    return [cx / (3.0 * area_twice), cy / (3.0 * area_twice)]


def _polyline_intersections(a, b):
    hits = []
    for a1, a2 in zip(a, a[1:]):
        for b1, b2 in zip(b, b[1:]):
            hit = _segment_intersection(a1, a2, b1, b2)
            if hit is not None:
                hits.append(hit)
    return hits


def _segment_intersection(a, b, c, d):
    ax, ay, bx, by, cx, cy, dx, dy = a[0], a[1], b[0], b[1], c[0], c[1], d[0], d[1]
    denom = (ax - bx) * (cy - dy) - (ay - by) * (cx - dx)
    if abs(denom) <= 1e-12:
        return None
    px = ((ax * by - ay * bx) * (cx - dx) - (ax - bx) * (cx * dy - cy * dx)) / denom
    py = ((ax * by - ay * bx) * (cy - dy) - (ay - by) * (cx * dy - cy * dx)) / denom
    if min(ax, bx) - 1e-9 <= px <= max(ax, bx) + 1e-9 and min(ay, by) - 1e-9 <= py <= max(ay, by) + 1e-9 and min(cx, dx) - 1e-9 <= px <= max(cx, dx) + 1e-9 and min(cy, dy) - 1e-9 <= py <= max(cy, dy) + 1e-9:
        return [px, py]
    return None


def _decode_gpkg_geometry(blob):
    data = bytes(blob)
    if data[:2] != b"GP":
        return _decode_wkb(data)
    flags = data[3]
    endian = "<" if flags & 1 else ">"
    envelope_code = (flags >> 1) & 0b111
    envelope_sizes = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}
    offset = 8 + envelope_sizes.get(envelope_code, 0)
    return _decode_wkb(data[offset:])


def _decode_wkb(data):
    endian = "<" if data[0] == 1 else ">"
    geom_type = struct.unpack(endian + "I", data[1:5])[0]
    offset = 5
    if geom_type == 1:
        x, y = struct.unpack(endian + "2d", data[offset:offset + 16])
        return [x, y]
    if geom_type == 2:
        count = struct.unpack(endian + "I", data[offset:offset + 4])[0]
        offset += 4
        return [list(struct.unpack(endian + "2d", data[offset + i * 16:offset + (i + 1) * 16])) for i in range(count)]
    if geom_type == 3:
        rings = struct.unpack(endian + "I", data[offset:offset + 4])[0]
        offset += 4
        polygons = []
        for _ in range(rings):
            count = struct.unpack(endian + "I", data[offset:offset + 4])[0]
            offset += 4
            ring = [list(struct.unpack(endian + "2d", data[offset + i * 16:offset + (i + 1) * 16])) for i in range(count)]
            offset += count * 16
            polygons.append(ring)
        return polygons
    raise ValueError(f"Unsupported GeoPackage WKB geometry type {geom_type}.")


def _first_line(coordinates):
    if not coordinates:
        return []
    if isinstance(coordinates[0], (int, float)):
        return [coordinates]
    if coordinates and isinstance(coordinates[0], list) and coordinates[0] and isinstance(coordinates[0][0], (int, float)):
        return coordinates
    return _first_line(coordinates[0])


def _first_polygon(coordinates):
    if not coordinates:
        return []
    if coordinates and isinstance(coordinates[0], list) and coordinates[0] and isinstance(coordinates[0][0], (int, float)):
        return coordinates
    return _first_polygon(coordinates[0])

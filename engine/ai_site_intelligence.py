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
class AISiteIntelligenceSettings:
    """Deterministic site intelligence settings."""

    maximum_buildable_slope: float = 12.0
    preferred_buildable_slope: float = 5.0
    minimum_road_access_distance: float = 60.0
    minimum_utility_clearance: float = 2.0
    setback_distance: float = 5.0
    north_azimuth: float = 0.0
    prevailing_wind_azimuth: float = 270.0
    rainfall_intensity: float = 50.0
    flood_accumulation_threshold: int = 5
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "maximum_buildable_slope": self.maximum_buildable_slope,
            "preferred_buildable_slope": self.preferred_buildable_slope,
            "minimum_road_access_distance": self.minimum_road_access_distance,
            "minimum_utility_clearance": self.minimum_utility_clearance,
            "setback_distance": self.setback_distance,
            "north_azimuth": self.north_azimuth,
            "prevailing_wind_azimuth": self.prevailing_wind_azimuth,
            "rainfall_intensity": self.rainfall_intensity,
            "flood_accumulation_threshold": self.flood_accumulation_threshold,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return AISiteIntelligenceSettings(
            _f(data.get("maximum_buildable_slope"), 12.0),
            _f(data.get("preferred_buildable_slope"), 5.0),
            _f(data.get("minimum_road_access_distance"), 60.0),
            _f(data.get("minimum_utility_clearance"), 2.0),
            _f(data.get("setback_distance"), 5.0),
            _f(data.get("north_azimuth"), 0.0),
            _f(data.get("prevailing_wind_azimuth"), 270.0),
            _f(data.get("rainfall_intensity"), 50.0),
            int(data.get("flood_accumulation_threshold", 5)),
            dict(data.get("metadata", {})),
        )


@dataclass
class AISiteValidationReport:
    """AI Site Intelligence validation result."""

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
        return AISiteValidationReport(
            bool(data.get("valid", True)),
            list(data.get("issues", [])),
            list(data.get("warnings", [])),
            dict(data.get("statistics", {})),
            data.get("generated_at", _timestamp()),
        )


@dataclass
class AISiteDiagnostics:
    """AI Site Intelligence diagnostics summary."""

    analyses: int = 0
    recommendations: int = 0
    constraints: int = 0
    reports: int = 0
    validation_issues: int = 0
    updated_at: str = field(default_factory=_timestamp)

    def to_dict(self):
        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        data = data or {}
        return AISiteDiagnostics(
            int(data.get("analyses", 0)),
            int(data.get("recommendations", 0)),
            int(data.get("constraints", 0)),
            int(data.get("reports", 0)),
            int(data.get("validation_issues", 0)),
            data.get("updated_at", _timestamp()),
        )


@dataclass
class AISiteIntelligenceProject:
    """Deterministic AI Site Intelligence project metadata."""

    name: str = "AI Site Intelligence"
    settings: AISiteIntelligenceSettings = field(default_factory=AISiteIntelligenceSettings)
    knowledge_base: dict = field(default_factory=dict)
    intelligence_metadata: dict = field(default_factory=dict)
    buildability_reports: list = field(default_factory=list)
    environmental_reports: list = field(default_factory=list)
    planning_reports: list = field(default_factory=list)
    constraint_reports: list = field(default_factory=list)
    engineering_reports: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    validation_report: AISiteValidationReport = field(default_factory=AISiteValidationReport)
    diagnostics: AISiteDiagnostics = field(default_factory=AISiteDiagnostics)
    visualization_metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    version_metadata: dict = field(default_factory=lambda: {"release": "2.0", "batch": "E"})

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "settings": self.settings.to_dict(),
            "knowledge_base": dict(self.knowledge_base),
            "intelligence_metadata": dict(self.intelligence_metadata),
            "buildability_reports": [dict(item) for item in self.buildability_reports],
            "environmental_reports": [dict(item) for item in self.environmental_reports],
            "planning_reports": [dict(item) for item in self.planning_reports],
            "constraint_reports": [dict(item) for item in self.constraint_reports],
            "engineering_reports": [dict(item) for item in self.engineering_reports],
            "recommendations": [dict(item) for item in self.recommendations],
            "validation_report": self.validation_report.to_dict(),
            "diagnostics": self.diagnostics.to_dict(),
            "visualization_metadata": dict(self.visualization_metadata),
            "version_metadata": dict(self.version_metadata),
        }

    @staticmethod
    def from_dict(data):
        data = data or {}
        return AISiteIntelligenceProject(
            data.get("name", "AI Site Intelligence"),
            AISiteIntelligenceSettings.from_dict(data.get("settings", {})),
            dict(data.get("knowledge_base", {})),
            dict(data.get("intelligence_metadata", {})),
            [dict(item) for item in data.get("buildability_reports", [])],
            [dict(item) for item in data.get("environmental_reports", [])],
            [dict(item) for item in data.get("planning_reports", [])],
            [dict(item) for item in data.get("constraint_reports", [])],
            [dict(item) for item in data.get("engineering_reports", [])],
            [dict(item) for item in data.get("recommendations", [])],
            AISiteValidationReport.from_dict(data.get("validation_report", {})),
            AISiteDiagnostics.from_dict(data.get("diagnostics", {})),
            dict(data.get("visualization_metadata", {})),
            data.get("id", str(uuid4())),
            dict(data.get("version_metadata", {"release": "2.0", "batch": "E"})),
        )


class AISiteIntelligenceManager:
    """Deterministic engineering intelligence over existing GIS, terrain, site and infrastructure data."""

    def __init__(self, infrastructure_manager=None):
        self.infrastructure_manager = infrastructure_manager
        self.projects = []
        self.active_project_id = None

    @property
    def active_project(self):
        if not self.projects:
            return None
        return self.get_project(self.active_project_id) or self.projects[-1]

    def create_project(self, name="AI Site Intelligence", settings=None, metadata=None):
        project = AISiteIntelligenceProject(
            name,
            settings if isinstance(settings, AISiteIntelligenceSettings) else AISiteIntelligenceSettings.from_dict(settings or {}),
            _default_knowledge_base(),
            dict(metadata or {}),
        )
        self.projects.append(project)
        self.active_project_id = project.id
        self.refresh_diagnostics(project)
        return project

    def ensure_project(self):
        return self.active_project or self.create_project()

    def get_project(self, project):
        if isinstance(project, AISiteIntelligenceProject):
            return project if project in self.projects else None
        return next((item for item in self.projects if item.id == project or item.name == project), None)

    def analyze_buildability(self, terrain_surface=None, name="Buildability Analysis"):
        project = self.ensure_project()
        terrain = self._terrain_manager()
        surface = terrain.surface_for(terrain_surface) if terrain_surface is not None else (terrain.ensure_project().surfaces[0] if terrain.ensure_project().surfaces else None)
        if surface is None:
            raise ValueError("Buildability analysis requires an existing terrain surface.")
        slope_values = [_triangle_slope(surface.points, [surface.points[i] for i in tri]) for tri in surface.triangles]
        avg_slope = sum(slope_values) / len(slope_values) if slope_values else 0.0
        max_slope = max(slope_values) if slope_values else 0.0
        road_distance = _nearest_distance(_surface_centroid(surface), [point for road in self._infrastructure_project().roads for point in road.get("centerline", [])])
        utility_distance = _nearest_distance(_surface_centroid(surface), [node.get("point") for network in self._infrastructure_project().utility_networks for node in network.get("nodes", [])])
        drainage = self._latest_drainage(surface.id)
        flood_risk = _flood_risk_from_drainage(drainage, project.settings.flood_accumulation_threshold)
        slope_score = _score_lower(avg_slope, project.settings.preferred_buildable_slope, project.settings.maximum_buildable_slope)
        access_score = _score_lower(road_distance, 0.0, project.settings.minimum_road_access_distance)
        utility_score = _score_lower(utility_distance, 0.0, max(project.settings.minimum_road_access_distance, 1.0))
        flood_score = max(0.0, 100.0 - flood_risk)
        foundation_score = _foundation_score(avg_slope, max_slope, surface)
        score = _weighted_score([(slope_score, 0.35), (access_score, 0.2), (utility_score, 0.15), (flood_score, 0.15), (foundation_score, 0.15)])
        risks = []
        if max_slope > project.settings.maximum_buildable_slope:
            risks.append("Maximum terrain slope exceeds buildability threshold.")
        if road_distance > project.settings.minimum_road_access_distance:
            risks.append("Road access distance exceeds preferred construction access threshold.")
        if flood_risk > 50.0:
            risks.append("Drainage accumulation indicates elevated flood exposure.")
        report = {
            "id": str(uuid4()),
            "name": name,
            "surface_id": surface.id,
            "terrain_suitability": slope_score,
            "slope_suitability": slope_score,
            "foundation_suitability_metadata": {"score": foundation_score, "average_slope": avg_slope, "maximum_slope": max_slope},
            "accessibility_analysis": {"nearest_road_distance": road_distance, "nearest_utility_distance": utility_distance, "score": access_score},
            "construction_feasibility": score,
            "engineering_constraints": self._constraint_sources(),
            "risk_score": 100.0 - score,
            "risks": risks,
            "recommendations": _buildability_recommendations(score, risks),
            "created_at": _timestamp(),
            "validation": {"valid": True},
        }
        project.buildability_reports.append(report)
        self._add_recommendations(report["recommendations"], report["id"], "Buildability")
        self.refresh_diagnostics(project)
        return report

    def analyze_environment(self, terrain_surface=None, name="Environmental Analysis"):
        project = self.ensure_project()
        terrain = self._terrain_manager()
        surface = terrain.surface_for(terrain_surface) if terrain_surface is not None else (terrain.ensure_project().surfaces[0] if terrain.ensure_project().surfaces else None)
        if surface is None:
            raise ValueError("Environmental analysis requires an existing terrain surface.")
        aspect_values = [terrain.aspect_at(surface, point[0], point[1]) for point in surface.points]
        south_exposure = sum(_orientation_score(aspect, 180.0) for aspect in aspect_values) / len(aspect_values)
        north_exposure = sum(_orientation_score(aspect, project.settings.north_azimuth) for aspect in aspect_values) / len(aspect_values)
        wind_exposure = sum(_orientation_score(aspect, project.settings.prevailing_wind_azimuth) for aspect in aspect_values) / len(aspect_values)
        drainage = self._latest_drainage(surface.id)
        flood_risk = _flood_risk_from_drainage(drainage, project.settings.flood_accumulation_threshold)
        water_flow = _water_flow_influence(drainage)
        environmental_score = _weighted_score([(south_exposure, 0.25), (100.0 - flood_risk, 0.3), (100.0 - wind_exposure * 0.35, 0.15), (100.0 - min(project.settings.rainfall_intensity, 100.0), 0.1), (water_flow, 0.2)])
        report = {
            "id": str(uuid4()),
            "name": name,
            "surface_id": surface.id,
            "solar_orientation": {"south_exposure_score": south_exposure, "north_orientation": project.settings.north_azimuth},
            "sun_exposure": south_exposure,
            "north_orientation": project.settings.north_azimuth,
            "wind_metadata": {"prevailing_wind_azimuth": project.settings.prevailing_wind_azimuth, "exposure_score": wind_exposure},
            "rainfall_metadata": {"rainfall_intensity": project.settings.rainfall_intensity},
            "flood_risk_metadata": {"risk_score": flood_risk, "source": "terrain drainage accumulation"},
            "water_flow_influence": water_flow,
            "environmental_suitability": environmental_score,
            "recommendations": _environment_recommendations(environmental_score, flood_risk, south_exposure),
            "created_at": _timestamp(),
            "validation": {"valid": True},
        }
        project.environmental_reports.append(report)
        self._add_recommendations(report["recommendations"], report["id"], "Environmental")
        self.refresh_diagnostics(project)
        return report

    def plan_site(self, terrain_surface=None, name="Intelligent Site Planning"):
        project = self.ensure_project()
        terrain = self._terrain_manager()
        surface = terrain.surface_for(terrain_surface) if terrain_surface is not None else (terrain.ensure_project().surfaces[0] if terrain.ensure_project().surfaces else None)
        if surface is None:
            raise ValueError("Site planning requires an existing terrain surface.")
        constraints = self.detect_constraints(surface)
        candidates = []
        roads = self._infrastructure_project().roads
        utilities = self._infrastructure_project().utility_networks
        for point in surface.points:
            if _point_blocked(point, constraints["constraints"]):
                continue
            slope = terrain.slope_at(surface, point[0], point[1])
            road_distance = _nearest_distance(point, [p for road in roads for p in road.get("centerline", [])])
            utility_distance = _nearest_distance(point, [node.get("point") for network in utilities for node in network.get("nodes", [])])
            score = _weighted_score([
                (_score_lower(slope, 0.0, project.settings.maximum_buildable_slope), 0.45),
                (_score_lower(road_distance, 0.0, project.settings.minimum_road_access_distance), 0.3),
                (_score_lower(utility_distance, 0.0, project.settings.minimum_road_access_distance), 0.25),
            ])
            candidates.append({"point": list(point), "score": score, "slope": slope, "road_distance": road_distance, "utility_distance": utility_distance})
        candidates.sort(key=lambda item: item["score"], reverse=True)
        best = candidates[:5]
        parking = sorted(best, key=lambda item: item["road_distance"])[:3]
        service = sorted(best, key=lambda item: item["utility_distance"])[:3]
        report = {
            "id": str(uuid4()),
            "name": name,
            "surface_id": surface.id,
            "building_placement_suggestions": best,
            "road_access_suggestions": _road_access_suggestions(best, roads),
            "parking_location_suggestions": parking,
            "service_access_suggestions": service,
            "open_space_recommendations": _open_space_recommendations(self._infrastructure_project().parcels, constraints["constraints"]),
            "development_zones": _development_zones(best),
            "constraint_aware_planning": {"constraints_used": len(constraints["constraints"]), "candidate_count": len(candidates)},
            "engineering_validation": {"valid": bool(best), "message": "At least one buildable candidate found." if best else "No buildable candidates found."},
            "created_at": _timestamp(),
        }
        project.planning_reports.append(report)
        self._add_recommendations(_planning_recommendations(report), report["id"], "Planning")
        self.refresh_diagnostics(project)
        return report

    def detect_constraints(self, terrain_surface=None, name="Constraint Intelligence"):
        project = self.ensure_project()
        terrain = self._terrain_manager()
        surface = terrain.surface_for(terrain_surface) if terrain_surface is not None else (terrain.ensure_project().surfaces[0] if terrain.ensure_project().surfaces else None)
        constraints = []
        site = self._site_project()
        for boundary in site.boundaries:
            btype = boundary.get("boundary_type", "").lower()
            if any(token in btype for token in ("protected", "setback", "construction limit", "constraint", "zone")):
                constraints.append({"type": boundary.get("boundary_type"), "name": boundary.get("name"), "polygon": boundary.get("polygon", []), "severity": "High" if "protected" in btype else "Medium", "source": "Site Engineering"})
        if surface is not None:
            steep = [point for point in surface.points if terrain.slope_at(surface, point[0], point[1]) > project.settings.maximum_buildable_slope]
            if steep:
                constraints.append({"type": "Slope Restriction", "name": "Steep Terrain", "point_count": len(steep), "severity": "High", "source": "Terrain"})
        drainage = self._latest_drainage(surface.id if surface is not None else None)
        if drainage:
            flood_points = [item for item in drainage.get("low_points", []) if item.get("accumulation", 0) >= project.settings.flood_accumulation_threshold]
            if flood_points:
                constraints.append({"type": "Flood Constraint", "name": "Low Accumulation Areas", "low_points": flood_points, "severity": "High", "source": "Drainage"})
        utility_conflicts = _utility_conflicts(self._infrastructure_project().utility_networks, self._infrastructure_project().parcels, project.settings.minimum_utility_clearance)
        constraints.extend(utility_conflicts)
        report = {
            "id": str(uuid4()),
            "name": name,
            "constraints": constraints,
            "protected_zones": [item for item in constraints if "protected" in item.get("type", "").lower()],
            "setbacks": [item for item in constraints if "setback" in item.get("type", "").lower()],
            "slope_restrictions": [item for item in constraints if item.get("type") == "Slope Restriction"],
            "flood_constraints": [item for item in constraints if item.get("type") == "Flood Constraint"],
            "environmental_constraints": [item for item in constraints if item.get("source") in {"Drainage", "Terrain"}],
            "infrastructure_constraints": [item for item in constraints if item.get("source") == "Infrastructure"],
            "utility_conflicts": utility_conflicts,
            "engineering_conflict_detection": {"conflict_count": len([item for item in constraints if item.get("severity") == "High"])},
            "created_at": _timestamp(),
            "validation": {"valid": True},
        }
        if name:
            project.constraint_reports.append(report)
            self.refresh_diagnostics(project)
        return report

    def generate_reports(self, name="AI Site Intelligence Summary"):
        project = self.ensure_project()
        latest_build = project.buildability_reports[-1] if project.buildability_reports else None
        latest_env = project.environmental_reports[-1] if project.environmental_reports else None
        latest_plan = project.planning_reports[-1] if project.planning_reports else None
        latest_constraints = project.constraint_reports[-1] if project.constraint_reports else None
        risk = max([_f(item.get("risk_score")) for item in project.buildability_reports] or [0.0])
        report = {
            "id": str(uuid4()),
            "name": name,
            "site_suitability_report": latest_build,
            "environmental_report": latest_env,
            "buildability_report": latest_build,
            "engineering_recommendation_report": list(project.recommendations),
            "constraint_report": latest_constraints,
            "risk_report": {"maximum_risk_score": risk, "risk_level": _risk_level(risk)},
            "summary_report": {
                "buildability_score": latest_build.get("construction_feasibility") if latest_build else None,
                "environmental_score": latest_env.get("environmental_suitability") if latest_env else None,
                "planning_candidates": len(latest_plan.get("building_placement_suggestions", [])) if latest_plan else 0,
                "constraint_count": len(latest_constraints.get("constraints", [])) if latest_constraints else 0,
            },
            "created_at": _timestamp(),
        }
        project.engineering_reports.append(report)
        self.refresh_diagnostics(project)
        return report

    def validate_project(self):
        project = self.ensure_project()
        issues, warnings = [], []
        if self.infrastructure_manager is None:
            issues.append("AI Site Intelligence requires the existing Infrastructure Manager.")
        if not self._terrain_manager().ensure_project().surfaces:
            issues.append("AI Site Intelligence requires terrain data.")
        for report in project.buildability_reports + project.environmental_reports + project.constraint_reports:
            if not report.get("validation", {}).get("valid", False):
                issues.append(f"Invalid intelligence report '{report.get('name')}'.")
        for rec in project.recommendations:
            if "basis" not in rec or "action" not in rec:
                issues.append("Recommendation is missing deterministic basis or action metadata.")
        if not project.recommendations:
            warnings.append("No AI Site Intelligence recommendations generated yet.")
        project.validation_report = AISiteValidationReport(not issues, issues, warnings, self.refresh_diagnostics(project).to_dict())
        return project.validation_report

    def visualization_metadata(self):
        project = self.ensure_project()
        project.visualization_metadata = {
            "suitability_overlays": {item["id"]: {"score": item["construction_feasibility"], "surface_id": item["surface_id"]} for item in project.buildability_reports},
            "constraint_overlays": {item["id"]: {"constraints": item["constraints"]} for item in project.constraint_reports},
            "recommendation_overlays": {item["id"]: {"action": item["action"], "priority": item["priority"]} for item in project.recommendations},
            "solar_overlays": {item["id"]: item["solar_orientation"] for item in project.environmental_reports},
            "wind_overlays": {item["id"]: item["wind_metadata"] for item in project.environmental_reports},
            "flood_overlays": {item["id"]: item["flood_risk_metadata"] for item in project.environmental_reports},
            "engineering_diagnostics": project.diagnostics.to_dict(),
        }
        return project.visualization_metadata

    def refresh_diagnostics(self, project=None):
        project = project or self.ensure_project()
        project.diagnostics = AISiteDiagnostics(
            len(project.buildability_reports) + len(project.environmental_reports) + len(project.planning_reports) + len(project.constraint_reports),
            len(project.recommendations),
            sum(len(item.get("constraints", [])) for item in project.constraint_reports),
            len(project.engineering_reports),
            len(project.validation_report.issues),
        )
        return project.diagnostics

    def to_dict(self):
        return {"active_project_id": self.active_project_id, "projects": [project.to_dict() for project in self.projects]}

    def from_dict(self, data):
        data = data or {}
        self.projects = [AISiteIntelligenceProject.from_dict(item) for item in data.get("projects", [])]
        self.active_project_id = data.get("active_project_id") or (self.projects[-1].id if self.projects else None)

    def clear(self):
        self.projects.clear()
        self.active_project_id = None

    def _add_recommendations(self, recommendations, report_id, category):
        project = self.ensure_project()
        for item in recommendations:
            record = {
                "id": str(uuid4()),
                "category": category,
                "source_report_id": report_id,
                "action": item["action"],
                "basis": item["basis"],
                "priority": item["priority"],
                "command_recommendation": item.get("command_recommendation", {}),
                "created_at": _timestamp(),
            }
            project.recommendations.append(record)

    def _terrain_manager(self):
        site = getattr(self.infrastructure_manager, "site_engineering_manager", None)
        terrain = getattr(site, "terrain_manager", None)
        if terrain is None:
            raise ValueError("AI Site Intelligence requires the existing Terrain Manager.")
        return terrain

    def _site_project(self):
        site = self.infrastructure_manager.site_engineering_manager
        return site.ensure_project()

    def _infrastructure_project(self):
        return self.infrastructure_manager.ensure_project()

    def _latest_drainage(self, surface_id):
        reports = self._site_project().drainage_reports
        for report in reversed(reports):
            if surface_id is None or report.get("surface_id") == surface_id:
                return report
        return None

    def _constraint_sources(self):
        return {
            "site_boundaries": len(self._site_project().boundaries),
            "roads": len(self._infrastructure_project().roads),
            "utilities": len(self._infrastructure_project().utility_networks),
            "parcels": len(self._infrastructure_project().parcels),
        }


def _default_knowledge_base():
    return {
        "buildability": {"preferred_slope_percent": 5.0, "maximum_slope_percent": 12.0},
        "environment": {"south_orientation_azimuth": 180.0, "flood_threshold_source": "drainage accumulation"},
        "planning": {"primary_inputs": ["terrain", "roads", "utilities", "parcels", "site constraints"]},
        "constraints": {"severity_order": ["Low", "Medium", "High"]},
    }


def _surface_centroid(surface):
    if not surface.points:
        return [0.0, 0.0, 0.0]
    return [sum(p[0] for p in surface.points) / len(surface.points), sum(p[1] for p in surface.points) / len(surface.points), sum(p[2] for p in surface.points) / len(surface.points)]


def _triangle_slope(all_points, points):
    a, b, c = points
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    return abs(math.hypot(nx, ny) / max(abs(nz), 1e-12)) * 100.0


def _nearest_distance(point, candidates):
    clean = [candidate for candidate in candidates if candidate]
    if not clean:
        return 1e9
    return min(math.hypot(point[0] - item[0], point[1] - item[1]) for item in clean)


def _score_lower(value, preferred, maximum):
    if value <= preferred:
        return 100.0
    if value >= maximum:
        return 0.0
    return max(0.0, 100.0 * (maximum - value) / max(maximum - preferred, 1e-9))


def _weighted_score(items):
    total_weight = sum(weight for _, weight in items)
    return sum(score * weight for score, weight in items) / max(total_weight, 1e-9)


def _foundation_score(avg_slope, max_slope, surface):
    relief = (surface.bounds()[5] - surface.bounds()[2]) if surface.bounds() else 0.0
    slope_component = _score_lower(avg_slope, 2.0, 20.0)
    max_component = _score_lower(max_slope, 5.0, 35.0)
    relief_component = _score_lower(relief, 0.0, 15.0)
    return _weighted_score([(slope_component, 0.4), (max_component, 0.4), (relief_component, 0.2)])


def _flood_risk_from_drainage(drainage, threshold):
    if not drainage:
        return 0.0
    accumulations = [_f(value) for value in drainage.get("flow_accumulation", {}).values()]
    if not accumulations:
        return 0.0
    high = max(accumulations)
    return min(100.0, high / max(threshold, 1) * 25.0)


def _water_flow_influence(drainage):
    if not drainage:
        return 100.0
    low_points = len(drainage.get("low_points", []))
    paths = len(drainage.get("drainage_paths", []))
    return max(0.0, 100.0 - low_points * 8.0 - paths * 2.0)


def _orientation_score(aspect, target):
    delta = abs((aspect - target + 180.0) % 360.0 - 180.0)
    return max(0.0, 100.0 * (1.0 - delta / 180.0))


def _buildability_recommendations(score, risks):
    recs = []
    if score < 70.0:
        recs.append({"action": "Refine grading strategy before building placement.", "basis": f"Buildability score {score:.2f} below production target.", "priority": "High", "command_recommendation": {"type": "site_grading_review"}})
    for risk in risks:
        recs.append({"action": "Resolve buildability risk.", "basis": risk, "priority": "High", "command_recommendation": {"type": "constraint_review"}})
    if not recs:
        recs.append({"action": "Proceed with detailed site planning on the highest-scoring terrain zones.", "basis": f"Buildability score {score:.2f} meets target.", "priority": "Medium", "command_recommendation": {"type": "site_planning"}})
    return recs


def _environment_recommendations(score, flood_risk, sun):
    recs = []
    if flood_risk > 40.0:
        recs.append({"action": "Reserve low accumulation areas for drainage or open space.", "basis": f"Flood risk score {flood_risk:.2f}.", "priority": "High", "command_recommendation": {"type": "drainage_constraint"}})
    if sun < 55.0:
        recs.append({"action": "Orient primary building frontage toward better solar exposure.", "basis": f"Sun exposure score {sun:.2f}.", "priority": "Medium", "command_recommendation": {"type": "orientation_review"}})
    if score >= 70.0:
        recs.append({"action": "Maintain current environmental planning assumptions.", "basis": f"Environmental suitability {score:.2f}.", "priority": "Low", "command_recommendation": {"type": "environment_monitoring"}})
    return recs


def _road_access_suggestions(candidates, roads):
    if not candidates or not roads:
        return []
    return [{"candidate": item["point"], "nearest_road_distance": item["road_distance"], "access_type": "driveway/service connection"} for item in candidates[:3]]


def _open_space_recommendations(parcels, constraints):
    blocked_names = {item.get("name") for item in constraints}
    return [{"parcel_id": parcel["id"], "parcel_name": parcel["name"], "area": parcel["area"], "basis": "High-area parcel available for open space reserve."} for parcel in parcels if parcel.get("name") not in blocked_names][:3]


def _development_zones(candidates):
    return [{"zone_id": str(uuid4()), "center": item["point"], "suitability": item["score"], "metadata": {"slope": item["slope"], "road_distance": item["road_distance"], "utility_distance": item["utility_distance"]}} for item in candidates[:5]]


def _planning_recommendations(report):
    if not report["building_placement_suggestions"]:
        return [{"action": "Revise constraints or grading to create a feasible development zone.", "basis": "No buildable candidates remained after constraints.", "priority": "High", "command_recommendation": {"type": "constraint_revision"}}]
    best = report["building_placement_suggestions"][0]
    return [{"action": "Use highest scoring point as initial building placement candidate.", "basis": f"Candidate score {best['score']:.2f} with slope {best['slope']:.2f}.", "priority": "Medium", "command_recommendation": {"type": "building_placement_metadata", "point": best["point"]}}]


def _point_blocked(point, constraints):
    for constraint in constraints:
        polygon = constraint.get("polygon")
        if polygon and _point_in_polygon(point, polygon):
            return True
    return False


def _utility_conflicts(networks, parcels, clearance):
    conflicts = []
    for network in networks:
        for node in network.get("nodes", []):
            point = node.get("point")
            for parcel in parcels:
                boundary = parcel.get("boundary", [])
                if _point_in_polygon(point, boundary) or _nearest_distance(point, boundary) < clearance:
                    conflicts.append({"type": "Utility Conflict", "name": f"{network.get('name')} vs {parcel.get('name')}", "network_id": network.get("id"), "parcel_id": parcel.get("id"), "severity": "High", "source": "Infrastructure"})
    return conflicts


def _point_in_polygon(point, polygon):
    x, y = point[0], point[1]
    inside = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        y1, y2 = a[1], b[1]
        if (y1 > y) != (y2 > y):
            x_cross = (b[0] - a[0]) * (y - y1) / max(y2 - y1, 1e-12) + a[0]
            if x < x_cross:
                inside = not inside
    return inside


def _risk_level(value):
    if value >= 70.0:
        return "High"
    if value >= 35.0:
        return "Medium"
    return "Low"

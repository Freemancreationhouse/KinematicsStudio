"""Daylight simulation foundation integrated with Simulation Workspace.

This module provides daylight and solar analysis data structures plus a
solver-interface implementation for static daylight studies. It consumes
explicit analysis points/openings, geographic metadata, sky metadata and solar
position data, then stores illuminance, daylight factor, sun exposure, shadow
and performance summaries in the existing simulation result database.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import acos, asin, atan2, cos, degrees, radians, sin, sqrt, tan
from uuid import uuid4


DAYLIGHT_STUDY_TYPES = {
    "Static Daylight",
    "Annual Daylight",
    "Building Daylight",
    "Interior Space",
    "Facade",
    "Urban",
}


SKY_MODEL_TYPES = {
    "Clear Sky",
    "Overcast Sky",
    "Intermediate Sky",
    "Custom Sky",
    "Uniform Sky",
    "Perez Sky",
    "CIE Sky",
}


OPENING_TYPES = {"Window", "Door", "Skylight", "Curtain Wall", "Facade Opening", "Atrium"}


@dataclass
class DaylightLocation:
    """Geographic and climate metadata for daylight studies."""

    study_id: str
    latitude: float
    longitude: float
    elevation: float = 0.0
    time_zone: float = 0.0
    north_orientation: float = 0.0
    site_metadata: dict = field(default_factory=dict)
    weather_metadata: dict = field(default_factory=dict)
    sky_condition_metadata: dict = field(default_factory=dict)
    season_metadata: dict = field(default_factory=dict)
    date: str = ""
    time: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe location metadata."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation": self.elevation,
            "time_zone": self.time_zone,
            "north_orientation": self.north_orientation,
            "site_metadata": dict(self.site_metadata),
            "weather_metadata": dict(self.weather_metadata),
            "sky_condition_metadata": dict(self.sky_condition_metadata),
            "season_metadata": dict(self.season_metadata),
            "date": self.date,
            "time": self.time,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create location metadata from persisted data."""

        data = data or {}
        return DaylightLocation(
            data.get("study_id", ""),
            float(data.get("latitude", 0.0)),
            float(data.get("longitude", 0.0)),
            float(data.get("elevation", 0.0)),
            float(data.get("time_zone", 0.0)),
            float(data.get("north_orientation", 0.0)),
            dict(data.get("site_metadata", {})),
            dict(data.get("weather_metadata", {})),
            dict(data.get("sky_condition_metadata", {})),
            dict(data.get("season_metadata", {})),
            data.get("date", ""),
            data.get("time", ""),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class SkyModel:
    """Sky luminance and type metadata for daylight analysis."""

    study_id: str
    name: str
    model_type: str
    luminance: float = 10000.0
    diffuse_illuminance: float = 10000.0
    direct_normal_illuminance: float = 50000.0
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe sky model data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "model_type": self.model_type,
            "luminance": self.luminance,
            "diffuse_illuminance": self.diffuse_illuminance,
            "direct_normal_illuminance": self.direct_normal_illuminance,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create sky model metadata from persisted data."""

        data = data or {}
        return SkyModel(
            data.get("study_id", ""),
            data.get("name", "Sky Model"),
            data.get("model_type", "Clear Sky"),
            float(data.get("luminance", 10000.0)),
            float(data.get("diffuse_illuminance", 10000.0)),
            float(data.get("direct_normal_illuminance", 50000.0)),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class DaylightOpening:
    """Building opening metadata for daylight studies."""

    study_id: str
    name: str
    opening_type: str
    target_references: list = field(default_factory=list)
    area: float = 1.0
    transmittance: float = 0.6
    orientation: dict = field(default_factory=dict)
    room_id: str = ""
    facade_id: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe opening data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "opening_type": self.opening_type,
            "target_references": [dict(item) for item in self.target_references],
            "area": self.area,
            "transmittance": self.transmittance,
            "orientation": dict(self.orientation),
            "room_id": self.room_id,
            "facade_id": self.facade_id,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create opening metadata from persisted data."""

        data = data or {}
        return DaylightOpening(
            data.get("study_id", ""),
            data.get("name", "Opening"),
            data.get("opening_type", "Window"),
            [dict(item) for item in data.get("target_references", [])],
            float(data.get("area", 1.0)),
            float(data.get("transmittance", 0.6)),
            dict(data.get("orientation", {})),
            data.get("room_id", ""),
            data.get("facade_id", ""),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class DaylightZone:
    """Room, facade, atrium or daylight zone metadata."""

    study_id: str
    name: str
    zone_type: str = "Room"
    area: float = 1.0
    target_references: list = field(default_factory=list)
    opening_ids: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe daylight zone data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "zone_type": self.zone_type,
            "area": self.area,
            "target_references": [dict(item) for item in self.target_references],
            "opening_ids": list(self.opening_ids),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create daylight zone metadata from persisted data."""

        data = data or {}
        return DaylightZone(
            data.get("study_id", ""),
            data.get("name", "Daylight Zone"),
            data.get("zone_type", "Room"),
            float(data.get("area", 1.0)),
            [dict(item) for item in data.get("target_references", [])],
            list(data.get("opening_ids", [])),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class DaylightExecutionRecord:
    """Execution history record for daylight studies."""

    study_id: str
    result_id: str = ""
    report_id: str = ""
    status: str = "Pending"
    started_at: str = ""
    completed_at: str = ""
    diagnostics: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe execution record data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "result_id": self.result_id,
            "report_id": self.report_id,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "diagnostics": dict(self.diagnostics),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create daylight execution history from persisted data."""

        data = data or {}
        return DaylightExecutionRecord(
            data.get("study_id", ""),
            data.get("result_id", ""),
            data.get("report_id", ""),
            data.get("status", "Pending"),
            data.get("started_at", ""),
            data.get("completed_at", ""),
            dict(data.get("diagnostics", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


class DaylightStaticSolver:
    """Static daylight solver registered through SimulationWorkspace."""

    solver_type = "Daylight Static"
    compatible_study_types = ["Daylight"]

    def solve(self, simulation_workspace, study):
        """Solve a static daylight study and return result metadata."""

        started_at = self._timestamp()
        validation = self.validate(simulation_workspace, study)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))
        mesh = simulation_workspace.mesh_for(study.mesh_definition_id)
        points = self._points(mesh)
        location = next(item for item in simulation_workspace.daylight_locations if item.study_id == study.id)
        sky = next(item for item in simulation_workspace.sky_models if item.study_id == study.id)
        openings = [item for item in simulation_workspace.daylight_openings if item.study_id == study.id]
        zones = [item for item in simulation_workspace.daylight_zones if item.study_id == study.id]
        solar = solar_position(location.latitude, location.longitude, location.time_zone, location.date, location.time)
        solar["shadow_direction"] = [-solar["solar_vector"][0], -solar["solar_vector"][1], -solar["solar_vector"][2]]
        point_results = {}
        values = []
        sun_hours = []
        exposure = []
        for point in points:
            result = self._point_illuminance(point, openings, sky, solar)
            point_results[point["id"]] = result
            values.append(result["lux"])
            sun_hours.append(result["sun_hours"])
            exposure.append(result["solar_exposure"])
        statistics = self._statistics(values, sun_hours, exposure, point_results, openings, zones)
        diagnostics = {
            "solver": self.solver_type,
            "started_at": started_at,
            "completed_at": self._timestamp(),
            "point_count": len(points),
            "opening_count": len(openings),
            "zone_count": len(zones),
            "converged": True,
            "static_daylight": True,
        }
        report = self._report(study, location, sky, solar, openings, zones, statistics, diagnostics)
        return {
            "result_type": "Static Daylight Result",
            "scalars": {
                "average_lux": statistics["average_lux"],
                "maximum_lux": statistics["maximum_lux"],
                "minimum_lux": statistics["minimum_lux"],
                "daylight_factor": statistics["daylight_factor"],
                "uniformity_ratio": statistics["uniformity_ratio"],
                "sun_hours": statistics["sun_hours"],
            },
            "vectors": {
                "illuminance_maps": point_results,
                "solar_vectors": {"sun": solar["solar_vector"], "shadow": solar["shadow_direction"]},
                "shadow_maps": {point_id: item["shadowed"] for point_id, item in point_results.items()},
            },
            "statistics": statistics,
            "reports": [report],
            "history": [{"event": "static_daylight_solve", "timestamp": diagnostics["completed_at"], "solver": self.solver_type}],
            "visualization_metadata": {
                "sun_path": solar,
                "contours": ["Illuminance", "Daylight Factor", "Solar Exposure"],
                "maps": ["Lux Heat Map", "Shadow Map", "Solar Exposure Map"],
                "color_legends": {
                    "lux": {"min": statistics["minimum_lux"], "max": statistics["maximum_lux"]},
                    "daylight_factor": {"average": statistics["daylight_factor"]},
                },
            },
            "metadata": {
                "location": location.to_dict(),
                "sky": sky.to_dict(),
                "openings": [item.to_dict() for item in openings],
                "zones": [item.to_dict() for item in zones],
                "point_results": point_results,
                "solar": solar,
                "diagnostics": diagnostics,
            },
            "diagnostics": diagnostics,
            "report": report,
        }

    def validate(self, simulation_workspace, study):
        """Validate daylight study setup."""

        errors = []
        warnings = []
        if study is None:
            return {"valid": False, "errors": ["Daylight study was not found."], "warnings": []}
        if study.study_type != "Daylight":
            errors.append("Daylight solver requires a Daylight study.")
        if simulation_workspace.mesh_for(study.mesh_definition_id) is None:
            errors.append("Daylight study requires a mesh definition.")
        if not [item for item in simulation_workspace.daylight_locations if item.study_id == study.id]:
            errors.append("Daylight study requires geographic location metadata.")
        if not [item for item in simulation_workspace.sky_models if item.study_id == study.id]:
            errors.append("Daylight study requires a sky model.")
        if not [item for item in simulation_workspace.daylight_openings if item.study_id == study.id]:
            warnings.append("Daylight study has no building openings.")
        return {"valid": not errors, "errors": errors, "warnings": warnings}

    def _points(self, mesh):
        return [self._point(item, index) for index, item in enumerate(mesh.settings.get("points", mesh.settings.get("nodes", [])))]

    def _point(self, item, index):
        coordinates = item.get("coordinates", item)
        return {
            "id": item.get("id", f"daylight-point-{index + 1}"),
            "x": float(coordinates.get("x", 0.0)),
            "y": float(coordinates.get("y", 0.0)),
            "z": float(coordinates.get("z", 0.0)),
            "normal": dict(item.get("normal", {"x": 0.0, "y": 0.0, "z": 1.0})),
            "zone_id": item.get("zone_id", ""),
        }

    def _point_illuminance(self, point, openings, sky, solar):
        diffuse = sky.diffuse_illuminance * sum(opening.area * opening.transmittance for opening in openings) / max(len(openings), 1)
        direct = sky.direct_normal_illuminance * max(0.0, solar["solar_vector"][2])
        visibility = min(1.0, max(0.05, sum(opening.area for opening in openings) / max(10.0, len(openings))))
        lux = (diffuse * 0.08 + direct * 0.02) * visibility
        shadowed = solar["altitude"] <= 0.0
        if shadowed:
            lux *= 0.4
        daylight_factor = lux / max(sky.diffuse_illuminance, 1.0) * 100.0
        return {
            "lux": lux,
            "daylight_factor": daylight_factor,
            "surface_illuminance": lux,
            "point_illuminance": lux,
            "sky_visibility": visibility,
            "direct_sunlight": max(0.0, direct),
            "diffuse_daylight": diffuse,
            "solar_exposure": max(0.0, direct) * visibility,
            "sun_hours": 1.0 if direct > 0.0 and not shadowed else 0.0,
            "shadowed": shadowed,
            "reflection_metadata": {"first_bounce_factor": 0.15},
            "glare_metadata": {"risk": "Review" if lux > 2000.0 else "Low"},
        }

    def _statistics(self, values, sun_hours, exposure, point_results, openings, zones):
        average = sum(values or [0.0]) / max(len(values), 1)
        maximum = max(values or [0.0])
        minimum = min(values or [0.0])
        return {
            "average_lux": average,
            "maximum_lux": maximum,
            "minimum_lux": minimum,
            "uniformity_ratio": minimum / maximum if maximum > 0.0 else 0.0,
            "daylight_factor": sum(item["daylight_factor"] for item in point_results.values()) / max(len(point_results), 1),
            "sun_hours": sum(sun_hours),
            "sun_exposure": sum(exposure),
            "sda_metadata": {"points_above_300_lux": len([value for value in values if value >= 300.0]), "total_points": len(values)},
            "ase_metadata": {"points_above_1000_lux": len([value for value in values if value >= 1000.0]), "total_points": len(values)},
            "udi_metadata": {"points_between_100_2000_lux": len([value for value in values if 100.0 <= value <= 2000.0]), "total_points": len(values)},
            "glare_metadata": {"high_lux_points": len([value for value in values if value > 2000.0])},
            "window_performance": {item.id: {"name": item.name, "area": item.area, "transmittance": item.transmittance} for item in openings},
            "opening_performance": {item.id: item.area * item.transmittance for item in openings},
            "room_statistics": {item.id: {"name": item.name, "area": item.area, "opening_count": len(item.opening_ids)} for item in zones},
            "facade_statistics": {item.id: {"name": item.name, "opening_count": len([opening for opening in openings if opening.facade_id == item.id])} for item in zones if item.zone_type == "Facade"},
        }

    def _report(self, study, location, sky, solar, openings, zones, statistics, diagnostics):
        return {
            "id": str(uuid4()),
            "title": f"{study.name} Daylight Engineering Report",
            "study_id": study.id,
            "generated_at": diagnostics["completed_at"],
            "study_summary": {"name": study.name, "type": study.metadata.get("daylight_type", "Static Daylight"), "status": "Solved"},
            "location_summary": location.to_dict(),
            "climate_summary": {"weather": location.weather_metadata, "season": location.season_metadata},
            "sky_model": sky.to_dict(),
            "solar_analysis": solar,
            "room_summary": [item.to_dict() for item in zones if item.zone_type == "Room"],
            "window_summary": [item.to_dict() for item in openings if item.opening_type == "Window"],
            "facade_summary": [item.to_dict() for item in zones if item.zone_type == "Facade"],
            "lux_statistics": {"average": statistics["average_lux"], "maximum": statistics["maximum_lux"], "minimum": statistics["minimum_lux"]},
            "daylight_factor": statistics["daylight_factor"],
            "sun_hours": statistics["sun_hours"],
            "performance_summary": statistics,
            "warnings": [],
            "recommendations": self._recommendations(statistics),
        }

    def _recommendations(self, statistics):
        recommendations = []
        if statistics["average_lux"] < 300.0:
            recommendations.append("Increase effective opening area, glazing transmittance, or daylight redirection.")
        if statistics["uniformity_ratio"] < 0.2:
            recommendations.append("Review daylight distribution for excessive contrast.")
        return recommendations

    def _timestamp(self):
        return datetime.now(timezone.utc).isoformat()


def solar_position(latitude, longitude, time_zone, date, time):
    """Compute solar position metadata for the requested site date and time."""

    moment = _parse_datetime(date, time)
    day = int(moment.strftime("%j"))
    hour = moment.hour + moment.minute / 60.0 + moment.second / 3600.0
    gamma = 2.0 * 3.141592653589793 / 365.0 * (day - 1 + (hour - 12.0) / 24.0)
    declination = (
        0.006918
        - 0.399912 * cos(gamma)
        + 0.070257 * sin(gamma)
        - 0.006758 * cos(2 * gamma)
        + 0.000907 * sin(2 * gamma)
        - 0.002697 * cos(3 * gamma)
        + 0.00148 * sin(3 * gamma)
    )
    equation_of_time = 229.18 * (
        0.000075
        + 0.001868 * cos(gamma)
        - 0.032077 * sin(gamma)
        - 0.014615 * cos(2 * gamma)
        - 0.040849 * sin(2 * gamma)
    )
    true_solar_time = (hour * 60.0 + equation_of_time + 4.0 * longitude - 60.0 * time_zone) % 1440.0
    hour_angle = radians(true_solar_time / 4.0 - 180.0)
    latitude_rad = radians(latitude)
    altitude = asin(sin(latitude_rad) * sin(declination) + cos(latitude_rad) * cos(declination) * cos(hour_angle))
    azimuth = atan2(
        -sin(hour_angle),
        tan(declination) * cos(latitude_rad) - sin(latitude_rad) * cos(hour_angle),
    )
    vector = [cos(altitude) * sin(azimuth), cos(altitude) * cos(azimuth), sin(altitude)]
    return {
        "altitude": degrees(altitude),
        "azimuth": (degrees(azimuth) + 360.0) % 360.0,
        "declination": degrees(declination),
        "hour_angle": degrees(hour_angle),
        "true_solar_time": true_solar_time,
        "equation_of_time": equation_of_time,
        "solar_vector": vector,
        "sun_path": {"day_of_year": day, "hour": hour},
    }


def _parse_datetime(date, time):
    date_text = date or datetime.now(timezone.utc).date().isoformat()
    time_text = time or "12:00:00"
    if len(time_text.split(":")) == 2:
        time_text += ":00"
    return datetime.fromisoformat(f"{date_text}T{time_text}")

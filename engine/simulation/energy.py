"""Whole-building energy analysis integrated with Simulation Workspace.

The energy solver evaluates building energy demand from workspace-owned study
metadata. It reuses thermal material properties, daylight opening data,
existing results storage, and the shared solver interface. It does not own CAD
geometry, create meshes, or modify model data.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


ENERGY_STUDY_TYPES = {
    "Annual Energy Study",
    "Monthly Study",
    "Peak Load Study",
    "Building Energy Study",
    "Zone Energy Study",
    "Comparative Study",
}


ENERGY_ENVELOPE_TYPES = {
    "Wall",
    "Roof",
    "Floor",
    "Window",
    "Door",
    "Curtain Wall",
    "Shading Device",
    "Skylight",
}


ENERGY_SCHEDULE_TYPES = {
    "Occupancy",
    "Lighting",
    "Equipment",
    "HVAC",
    "Ventilation",
    "Domestic Hot Water",
    "Custom Schedule",
}


HVAC_SYSTEM_TYPES = {
    "Heating System",
    "Cooling System",
    "Ventilation System",
    "Heat Pump",
    "Boiler",
    "Chiller",
    "Air Handling Unit",
    "Terminal Unit",
}


@dataclass
class EnergyClimateProfile:
    """Reusable climate and weather metadata for an energy study."""

    study_id: str
    weather_metadata: dict = field(default_factory=dict)
    temperature_profile: list = field(default_factory=list)
    humidity_metadata: dict = field(default_factory=dict)
    wind_metadata: dict = field(default_factory=dict)
    solar_radiation_metadata: dict = field(default_factory=dict)
    cloud_cover_metadata: dict = field(default_factory=dict)
    rainfall_metadata: dict = field(default_factory=dict)
    heating_degree_days: float = 0.0
    cooling_degree_days: float = 0.0
    climate_zone: str = ""
    weather_file_metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe climate profile data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "weather_metadata": dict(self.weather_metadata),
            "temperature_profile": [float(item) for item in self.temperature_profile],
            "humidity_metadata": dict(self.humidity_metadata),
            "wind_metadata": dict(self.wind_metadata),
            "solar_radiation_metadata": dict(self.solar_radiation_metadata),
            "cloud_cover_metadata": dict(self.cloud_cover_metadata),
            "rainfall_metadata": dict(self.rainfall_metadata),
            "heating_degree_days": self.heating_degree_days,
            "cooling_degree_days": self.cooling_degree_days,
            "climate_zone": self.climate_zone,
            "weather_file_metadata": dict(self.weather_file_metadata),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a climate profile from persisted data."""

        data = data or {}
        return EnergyClimateProfile(
            data.get("study_id", ""),
            dict(data.get("weather_metadata", {})),
            [float(item) for item in data.get("temperature_profile", [])],
            dict(data.get("humidity_metadata", {})),
            dict(data.get("wind_metadata", {})),
            dict(data.get("solar_radiation_metadata", {})),
            dict(data.get("cloud_cover_metadata", {})),
            dict(data.get("rainfall_metadata", {})),
            float(data.get("heating_degree_days", 0.0)),
            float(data.get("cooling_degree_days", 0.0)),
            data.get("climate_zone", ""),
            dict(data.get("weather_file_metadata", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class EnergyEnvelopeElement:
    """Energy envelope metadata that references existing CAD geometry."""

    study_id: str
    name: str
    element_type: str
    area: float = 0.0
    u_value: float = 0.0
    orientation: dict = field(default_factory=dict)
    zone_id: str = ""
    material_references: list = field(default_factory=list)
    shading_metadata: dict = field(default_factory=dict)
    geometry_references: list = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe envelope element data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "element_type": self.element_type,
            "area": self.area,
            "u_value": self.u_value,
            "orientation": dict(self.orientation),
            "zone_id": self.zone_id,
            "material_references": [dict(item) for item in self.material_references],
            "shading_metadata": dict(self.shading_metadata),
            "geometry_references": [dict(item) for item in self.geometry_references],
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create envelope metadata from persisted data."""

        data = data or {}
        return EnergyEnvelopeElement(
            data.get("study_id", ""),
            data.get("name", "Envelope Element"),
            data.get("element_type", "Wall"),
            float(data.get("area", 0.0)),
            float(data.get("u_value", 0.0)),
            dict(data.get("orientation", {})),
            data.get("zone_id", ""),
            [dict(item) for item in data.get("material_references", [])],
            dict(data.get("shading_metadata", {})),
            [dict(item) for item in data.get("geometry_references", [])],
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class EnergySchedule:
    """Occupancy, lighting, equipment, HVAC, or ventilation schedule."""

    study_id: str
    name: str
    schedule_type: str
    values: list = field(default_factory=list)
    gains: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe schedule data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "schedule_type": self.schedule_type,
            "values": [float(item) for item in self.values],
            "gains": dict(self.gains),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a schedule from persisted data."""

        data = data or {}
        return EnergySchedule(
            data.get("study_id", ""),
            data.get("name", "Energy Schedule"),
            data.get("schedule_type", "Custom Schedule"),
            [float(item) for item in data.get("values", [])],
            dict(data.get("gains", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class HVACSystem:
    """HVAC system metadata for energy demand estimation."""

    study_id: str
    name: str
    system_type: str
    efficiency: float = 1.0
    capacity: float = 0.0
    control_metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe HVAC system data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "system_type": self.system_type,
            "efficiency": self.efficiency,
            "capacity": self.capacity,
            "control_metadata": dict(self.control_metadata),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create HVAC metadata from persisted data."""

        data = data or {}
        return HVACSystem(
            data.get("study_id", ""),
            data.get("name", "HVAC System"),
            data.get("system_type", "Heating System"),
            float(data.get("efficiency", 1.0)),
            float(data.get("capacity", 0.0)),
            dict(data.get("control_metadata", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class EnergyExecutionRecord:
    """Execution history record for an energy study."""

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
        """Return JSON-safe energy execution history."""

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
        """Create energy execution history from persisted data."""

        data = data or {}
        return EnergyExecutionRecord(
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


class EnergyBalanceSolver:
    """Whole-building energy balance solver registered through SimulationWorkspace."""

    solver_type = "Whole Building Energy Balance"
    compatible_study_types = ["Energy"]

    def solve(self, simulation_workspace, study):
        """Solve monthly and annual building energy demand for an energy study."""

        started_at = self._timestamp()
        validation = self.validate(simulation_workspace, study)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))

        climate = self._climate(simulation_workspace, study)
        envelope = self._envelope(simulation_workspace, study)
        schedules = [item for item in simulation_workspace.energy_schedules if item.study_id == study.id]
        hvac_systems = [item for item in simulation_workspace.hvac_systems if item.study_id == study.id]
        months = self._months()
        temperatures = self._monthly_values(climate.temperature_profile, 12, 18.0)
        solar = self._monthly_values(climate.solar_radiation_metadata.get("monthly_kwh_per_m2", []), 12, 120.0)
        floor_area = max(float(study.solver_settings.get("floor_area", self._floor_area(envelope))), 1.0)
        heating_setpoint = float(study.solver_settings.get("heating_setpoint", 20.0))
        cooling_setpoint = float(study.solver_settings.get("cooling_setpoint", 24.0))
        carbon_factor = float(study.solver_settings.get("carbon_factor_kg_per_kwh", 0.45))
        energy_rate = float(study.solver_settings.get("energy_rate_per_kwh", 0.0))
        renewable = float(study.solver_settings.get("renewable_contribution_kwh", 0.0))
        ua = self._ua(envelope, simulation_workspace)
        window_area = sum(item.area for item in envelope if item.element_type in {"Window", "Skylight", "Curtain Wall"})
        transmittance = self._average_transmittance(envelope)
        ventilation_rate = self._schedule_average(schedules, "Ventilation", "air_change_watts_per_k", 0.0)
        infiltration_rate = float(study.solver_settings.get("infiltration_watts_per_k", 0.0))
        heating_efficiency = self._hvac_efficiency(hvac_systems, {"Heating System", "Heat Pump", "Boiler"}, 0.9)
        cooling_efficiency = self._hvac_efficiency(hvac_systems, {"Cooling System", "Heat Pump", "Chiller"}, 3.0)

        monthly = []
        for index, month in enumerate(months):
            hours = month["hours"]
            outdoor = temperatures[index]
            heating_delta = max(0.0, heating_setpoint - outdoor)
            cooling_delta = max(0.0, outdoor - cooling_setpoint)
            transmission_heating = ua * heating_delta * hours / 1000.0
            transmission_cooling = ua * cooling_delta * hours / 1000.0
            ventilation_heating = (ventilation_rate + infiltration_rate) * heating_delta * hours / 1000.0
            ventilation_cooling = (ventilation_rate + infiltration_rate) * cooling_delta * hours / 1000.0
            solar_gain = solar[index] * window_area * transmittance
            internal = self._monthly_internal_gain(schedules, index, hours)
            lighting = self._monthly_gain(schedules, "Lighting", index, hours)
            equipment = self._monthly_gain(schedules, "Equipment", index, hours)
            heating_load = max(0.0, transmission_heating + ventilation_heating - internal - solar_gain)
            cooling_load = max(0.0, transmission_cooling + ventilation_cooling + internal + solar_gain)
            hvac_energy = heating_load / max(heating_efficiency, 0.01) + cooling_load / max(cooling_efficiency, 0.01)
            total = hvac_energy + lighting + equipment
            monthly.append({
                "month": month["name"],
                "outdoor_temperature": outdoor,
                "heating_load": heating_load,
                "cooling_load": cooling_load,
                "solar_gain": solar_gain,
                "internal_gains": internal,
                "lighting_energy": lighting,
                "equipment_energy": equipment,
                "hvac_energy": hvac_energy,
                "total_energy": total,
            })

        annual_energy = sum(item["total_energy"] for item in monthly)
        heating_demand = sum(item["heating_load"] for item in monthly)
        cooling_demand = sum(item["cooling_load"] for item in monthly)
        lighting_energy = sum(item["lighting_energy"] for item in monthly)
        equipment_energy = sum(item["equipment_energy"] for item in monthly)
        hvac_energy = sum(item["hvac_energy"] for item in monthly)
        peak_heating = max(item["heating_load"] for item in monthly)
        peak_cooling = max(item["cooling_load"] for item in monthly)
        eui = annual_energy / floor_area
        carbon = max(0.0, annual_energy - renewable) * carbon_factor
        cost = annual_energy * energy_rate
        balance_error = abs(annual_energy - (hvac_energy + lighting_energy + equipment_energy))
        zone_summary = self._zone_summary(envelope, monthly, floor_area)
        envelope_summary = self._envelope_summary(envelope, simulation_workspace)
        hvac_summary = self._hvac_summary(hvac_systems, hvac_energy)
        diagnostics = {
            "solver": self.solver_type,
            "started_at": started_at,
            "completed_at": self._timestamp(),
            "month_count": len(monthly),
            "envelope_element_count": len(envelope),
            "schedule_count": len(schedules),
            "hvac_system_count": len(hvac_systems),
            "thermal_reuse": bool(simulation_workspace.thermal_material_properties or simulation_workspace.thermal_assemblies),
            "daylight_reuse": bool(simulation_workspace.daylight_openings or simulation_workspace.daylight_zones),
            "energy_balance_error": balance_error,
            "converged": True,
        }
        statistics = {
            "annual_energy_use": annual_energy,
            "energy_use_intensity": eui,
            "heating_demand": heating_demand,
            "cooling_demand": cooling_demand,
            "peak_heating": peak_heating,
            "peak_cooling": peak_cooling,
            "hvac_energy": hvac_energy,
            "lighting_energy": lighting_energy,
            "equipment_energy": equipment_energy,
            "renewable_contribution": renewable,
            "operational_carbon": carbon,
            "energy_cost": cost,
            "net_zero_readiness": renewable / max(annual_energy, 1.0),
            "energy_balance_error": balance_error,
            "floor_area": floor_area,
            "window_to_wall_ratio": self._window_to_wall_ratio(envelope),
            "monthly_profiles": monthly,
            "zone_summaries": zone_summary,
            "building_summary": {"floor_area": floor_area, "thermal_zone_count": len(zone_summary), "climate_zone": climate.climate_zone},
            "load_summaries": {"heating": heating_demand, "cooling": cooling_demand, "internal": sum(item["internal_gains"] for item in monthly)},
            "hvac_summaries": hvac_summary,
            "carbon_summaries": {"operational_carbon": carbon, "carbon_factor_kg_per_kwh": carbon_factor},
            "performance_indicators": {"eui": eui, "peak_heating": peak_heating, "peak_cooling": peak_cooling},
        }
        report = self._report(study, climate, envelope_summary, hvac_summary, statistics, diagnostics)
        return {
            "result_type": "Whole-Building Energy Result",
            "scalars": {
                "annual_energy_use": annual_energy,
                "energy_use_intensity": eui,
                "heating_demand": heating_demand,
                "cooling_demand": cooling_demand,
                "peak_heating": peak_heating,
                "peak_cooling": peak_cooling,
                "operational_carbon": carbon,
                "energy_cost": cost,
            },
            "vectors": {
                "monthly_profiles": monthly,
                "annual_profiles": [{"metric": "total_energy", "value": annual_energy}],
                "load_distribution": [{"month": item["month"], "heating": item["heating_load"], "cooling": item["cooling_load"]} for item in monthly],
                "thermal_zone_visualization": zone_summary,
                "envelope_performance": envelope_summary,
                "hvac_visualization": hvac_summary,
                "carbon_visualization": statistics["carbon_summaries"],
            },
            "statistics": statistics,
            "reports": [report],
            "history": [{"event": "whole_building_energy_solve", "timestamp": diagnostics["completed_at"], "solver": self.solver_type}],
            "visualization_metadata": {
                "dashboards": ["Energy Use", "EUI", "Peak Loads", "Operational Carbon"],
                "monthly_charts": ["Total Energy", "Heating", "Cooling", "HVAC", "Lighting", "Equipment"],
                "annual_charts": ["Energy End Uses", "Carbon", "Cost"],
                "color_legends": {
                    "energy_heat_map": {"min": min(item["total_energy"] for item in monthly), "max": max(item["total_energy"] for item in monthly)},
                    "load_distribution": {"heating_max": peak_heating, "cooling_max": peak_cooling},
                },
            },
            "metadata": {
                "diagnostics": diagnostics,
                "climate_profile_id": climate.id,
                "thermal_reuse": diagnostics["thermal_reuse"],
                "daylight_reuse": diagnostics["daylight_reuse"],
                "recommendations": report["recommendations"],
            },
            "diagnostics": diagnostics,
            "report": report,
        }

    def validate(self, simulation_workspace, study):
        """Validate energy study setup before execution."""

        errors = []
        warnings = []
        if study is None:
            return {"valid": False, "errors": ["Energy study was not found."], "warnings": []}
        if study.study_type != "Energy":
            errors.append("Energy solver requires an Energy study.")
        if not [item for item in simulation_workspace.energy_climate_profiles if item.study_id == study.id]:
            errors.append("Energy study requires climate and weather metadata.")
        envelope = [item for item in simulation_workspace.energy_envelope_elements if item.study_id == study.id]
        if not envelope:
            errors.append("Energy study requires building envelope metadata.")
        if not [item for item in simulation_workspace.hvac_systems if item.study_id == study.id]:
            warnings.append("Energy study has no HVAC systems; idealized system efficiencies will be used.")
        if not [item for item in simulation_workspace.energy_schedules if item.study_id == study.id]:
            warnings.append("Energy study has no occupancy, lighting, equipment, or ventilation schedules.")
        for element in envelope:
            if element.element_type not in ENERGY_ENVELOPE_TYPES:
                errors.append(f"Unsupported energy envelope type: {element.element_type}")
            if element.area <= 0.0:
                errors.append(f"Envelope element {element.name} requires positive area.")
            if element.u_value <= 0.0 and not element.material_references:
                errors.append(f"Envelope element {element.name} requires a U-value or material reference.")
            if not element.geometry_references:
                warnings.append(f"Envelope element {element.name} has no CAD geometry reference.")
        return {"valid": not errors, "errors": errors, "warnings": warnings}

    def _climate(self, simulation_workspace, study):
        return next(item for item in simulation_workspace.energy_climate_profiles if item.study_id == study.id)

    def _envelope(self, simulation_workspace, study):
        return [item for item in simulation_workspace.energy_envelope_elements if item.study_id == study.id]

    def _months(self):
        names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        return [{"name": name, "hours": day * 24.0} for name, day in zip(names, days)]

    def _monthly_values(self, values, count, default):
        values = [float(item) for item in values or []]
        if not values:
            return [default for _ in range(count)]
        if len(values) >= count:
            return values[:count]
        return values + [values[-1] for _ in range(count - len(values))]

    def _floor_area(self, envelope):
        floor_area = sum(item.area for item in envelope if item.element_type == "Floor")
        return floor_area or sum(item.area for item in envelope) * 0.25

    def _ua(self, envelope, simulation_workspace):
        return sum(item.area * self._u_value(item, simulation_workspace) for item in envelope if item.element_type != "Shading Device")

    def _u_value(self, element, simulation_workspace):
        if element.u_value > 0.0:
            return element.u_value
        material_ids = [item.get("material_id", item.get("id", "")) for item in element.material_references]
        u_values = []
        for material_id in material_ids:
            thermal = next((item for item in simulation_workspace.thermal_material_properties if item.material_id == material_id), None)
            if thermal is not None and thermal.u_value > 0.0:
                u_values.append(thermal.u_value)
            elif thermal is not None and thermal.thermal_resistance > 0.0:
                u_values.append(1.0 / thermal.thermal_resistance)
        return sum(u_values) / max(len(u_values), 1) if u_values else 1.0

    def _average_transmittance(self, envelope):
        transparent = [item for item in envelope if item.element_type in {"Window", "Skylight", "Curtain Wall"}]
        if not transparent:
            return 0.0
        values = [float(item.metadata.get("transmittance", item.shading_metadata.get("transmittance", 0.6))) for item in transparent]
        return sum(values) / max(len(values), 1)

    def _hvac_efficiency(self, systems, system_types, default):
        values = [item.efficiency for item in systems if item.system_type in system_types and item.efficiency > 0.0]
        return sum(values) / max(len(values), 1) if values else default

    def _schedule_average(self, schedules, schedule_type, gain_key, default):
        values = [float(item.gains.get(gain_key, default)) for item in schedules if item.schedule_type == schedule_type]
        return sum(values) / max(len(values), 1) if values else default

    def _monthly_internal_gain(self, schedules, index, hours):
        return (
            self._monthly_gain(schedules, "Occupancy", index, hours)
            + self._monthly_gain(schedules, "Lighting", index, hours)
            + self._monthly_gain(schedules, "Equipment", index, hours)
            + self._monthly_gain(schedules, "Domestic Hot Water", index, hours)
        )

    def _monthly_gain(self, schedules, schedule_type, index, hours):
        total = 0.0
        for schedule in schedules:
            if schedule.schedule_type != schedule_type:
                continue
            monthly = self._monthly_values(schedule.values, 12, float(schedule.gains.get("average_watts", 0.0)))
            watts = monthly[index]
            factor = float(schedule.gains.get("load_factor", 1.0))
            total += watts * factor * hours / 1000.0
        return total

    def _zone_summary(self, envelope, monthly, floor_area):
        zones = sorted({item.zone_id for item in envelope if item.zone_id})
        if not zones:
            zones = ["building"]
        annual = sum(item["total_energy"] for item in monthly)
        area_by_zone = {zone: sum(item.area for item in envelope if item.zone_id == zone and item.element_type == "Floor") for zone in zones}
        if not any(area_by_zone.values()):
            area_by_zone = {zone: floor_area / max(len(zones), 1) for zone in zones}
        total_area = sum(area_by_zone.values()) or floor_area
        return [
            {
                "zone_id": zone,
                "area": area,
                "annual_energy": annual * (area / total_area),
                "energy_use_intensity": annual * (area / total_area) / max(area, 1.0),
            }
            for zone, area in area_by_zone.items()
        ]

    def _window_to_wall_ratio(self, envelope):
        window_area = sum(item.area for item in envelope if item.element_type in {"Window", "Skylight", "Curtain Wall"})
        wall_area = sum(item.area for item in envelope if item.element_type in {"Wall", "Curtain Wall"})
        return window_area / max(wall_area, 1.0)

    def _envelope_summary(self, envelope, simulation_workspace):
        return [
            {
                "id": item.id,
                "name": item.name,
                "element_type": item.element_type,
                "area": item.area,
                "u_value": self._u_value(item, simulation_workspace),
                "zone_id": item.zone_id,
                "orientation": dict(item.orientation),
                "geometry_references": [dict(reference) for reference in item.geometry_references],
            }
            for item in envelope
        ]

    def _hvac_summary(self, systems, annual_hvac_energy):
        return [
            {
                "id": item.id,
                "name": item.name,
                "system_type": item.system_type,
                "efficiency": item.efficiency,
                "capacity": item.capacity,
                "annual_energy_share": annual_hvac_energy / max(len(systems), 1),
                "control_metadata": dict(item.control_metadata),
            }
            for item in systems
        ]

    def _report(self, study, climate, envelope_summary, hvac_summary, statistics, diagnostics):
        recommendations = []
        if statistics["energy_use_intensity"] > float(study.solver_settings.get("target_eui", 120.0)):
            recommendations.append("Reduce envelope losses, improve HVAC efficiency, or increase passive shading to lower EUI.")
        if statistics["window_to_wall_ratio"] > 0.45:
            recommendations.append("Review glazing ratio and shading strategy for cooling-load control.")
        if statistics["net_zero_readiness"] < 0.5 and statistics["annual_energy_use"] > 0.0:
            recommendations.append("Evaluate renewable contribution and load reduction strategies for net-zero readiness.")
        return {
            "id": str(uuid4()),
            "title": f"{study.name} Energy Engineering Report",
            "study_id": study.id,
            "building_summary": statistics["building_summary"],
            "climate_summary": {
                "climate_zone": climate.climate_zone,
                "heating_degree_days": climate.heating_degree_days,
                "cooling_degree_days": climate.cooling_degree_days,
                "weather_metadata": dict(climate.weather_metadata),
            },
            "envelope_summary": envelope_summary,
            "occupancy_summary": {"schedule_count": len([item for item in statistics["monthly_profiles"]])},
            "hvac_summary": hvac_summary,
            "annual_energy": statistics["annual_energy_use"],
            "monthly_energy": statistics["monthly_profiles"],
            "heating_loads": statistics["heating_demand"],
            "cooling_loads": statistics["cooling_demand"],
            "energy_intensity": statistics["energy_use_intensity"],
            "carbon_estimation": statistics["operational_carbon"],
            "performance_rating": self._performance_rating(statistics["energy_use_intensity"]),
            "passive_design_observations": {
                "window_to_wall_ratio": statistics["window_to_wall_ratio"],
                "solar_gain_total": sum(item["solar_gain"] for item in statistics["monthly_profiles"]),
            },
            "warnings": [],
            "recommendations": recommendations,
            "diagnostics": diagnostics,
        }

    def _performance_rating(self, eui):
        if eui <= 60.0:
            return "High Performance"
        if eui <= 120.0:
            return "Efficient"
        if eui <= 180.0:
            return "Needs Improvement"
        return "High Energy Demand"

    def _timestamp(self):
        return datetime.now(timezone.utc).isoformat()

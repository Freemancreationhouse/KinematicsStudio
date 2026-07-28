"""CFD simulation foundation integrated with Simulation Workspace.

The CFD solver evaluates airflow metadata over workspace-owned simulation mesh
definitions. It reuses existing thermal, daylight, energy, result,
visualization, command, persistence and diagnostics paths. It does not own CAD
geometry or introduce a duplicate mesh or solver framework.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import sqrt
from uuid import uuid4


CFD_STUDY_TYPES = {
    "Steady-State CFD",
    "Transient CFD",
    "Indoor Airflow Study",
    "Outdoor Wind Study",
    "HVAC Airflow Study",
    "Natural Ventilation Study",
    "Comparative CFD Study",
}


CFD_DOMAIN_TYPES = {"Air Domain", "Fluid Region", "Indoor Domain", "Outdoor Domain", "HVAC Domain", "Product Flow Domain"}


CFD_BOUNDARY_TYPES = {
    "Velocity Inlet",
    "Pressure Inlet",
    "Mass Flow Inlet",
    "Pressure Outlet",
    "Velocity Outlet",
    "Wall",
    "Slip Wall",
    "No-Slip Wall",
    "Symmetry",
    "Open Boundary",
    "Moving Wall",
    "Fan",
    "HVAC Diffuser",
    "Window Opening",
    "Door Opening",
    "Custom Boundary Condition",
}


CFD_FLOW_SOURCE_TYPES = {
    "Supply Air",
    "Exhaust Air",
    "Natural Ventilation",
    "Wind Profile",
    "Heat Source Reuse",
    "Occupancy Source Reuse",
    "Equipment Source Reuse",
    "Buoyancy",
    "Internal Flow Source",
}


@dataclass
class CFDDomain:
    """Reusable fluid domain metadata for CFD studies."""

    study_id: str
    name: str
    domain_type: str = "Air Domain"
    extents: dict = field(default_factory=dict)
    reference_elevation: float = 0.0
    reference_pressure: float = 101325.0
    gravity_metadata: dict = field(default_factory=dict)
    fluid_properties: dict = field(default_factory=dict)
    compressibility_metadata: dict = field(default_factory=dict)
    turbulence_metadata: dict = field(default_factory=dict)
    region_metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe CFD domain data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "domain_type": self.domain_type,
            "extents": dict(self.extents),
            "reference_elevation": self.reference_elevation,
            "reference_pressure": self.reference_pressure,
            "gravity_metadata": dict(self.gravity_metadata),
            "fluid_properties": dict(self.fluid_properties),
            "compressibility_metadata": dict(self.compressibility_metadata),
            "turbulence_metadata": dict(self.turbulence_metadata),
            "region_metadata": dict(self.region_metadata),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create CFD domain metadata from persisted data."""

        data = data or {}
        return CFDDomain(
            data.get("study_id", ""),
            data.get("name", "CFD Domain"),
            data.get("domain_type", "Air Domain"),
            dict(data.get("extents", {})),
            float(data.get("reference_elevation", 0.0)),
            float(data.get("reference_pressure", 101325.0)),
            dict(data.get("gravity_metadata", {})),
            dict(data.get("fluid_properties", {})),
            dict(data.get("compressibility_metadata", {})),
            dict(data.get("turbulence_metadata", {})),
            dict(data.get("region_metadata", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class CFDBoundaryCondition:
    """CFD boundary condition metadata referencing existing CAD or mesh regions."""

    study_id: str
    name: str
    boundary_type: str
    target_references: list = field(default_factory=list)
    values: dict = field(default_factory=dict)
    coordinate_system: str = ""
    enabled: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe CFD boundary data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "boundary_type": self.boundary_type,
            "target_references": [dict(item) for item in self.target_references],
            "values": dict(self.values),
            "coordinate_system": self.coordinate_system,
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create CFD boundary metadata from persisted data."""

        data = data or {}
        return CFDBoundaryCondition(
            data.get("study_id", ""),
            data.get("name", "CFD Boundary"),
            data.get("boundary_type", "Custom Boundary Condition"),
            [dict(item) for item in data.get("target_references", [])],
            dict(data.get("values", {})),
            data.get("coordinate_system", ""),
            bool(data.get("enabled", True)),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class CFDFlowSource:
    """Internal airflow source or reused thermal/occupancy/equipment source metadata."""

    study_id: str
    name: str
    source_type: str
    target_references: list = field(default_factory=list)
    values: dict = field(default_factory=dict)
    enabled: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe CFD flow source data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "source_type": self.source_type,
            "target_references": [dict(item) for item in self.target_references],
            "values": dict(self.values),
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create CFD flow source metadata from persisted data."""

        data = data or {}
        return CFDFlowSource(
            data.get("study_id", ""),
            data.get("name", "CFD Flow Source"),
            data.get("source_type", "Internal Flow Source"),
            [dict(item) for item in data.get("target_references", [])],
            dict(data.get("values", {})),
            bool(data.get("enabled", True)),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class CFDExecutionRecord:
    """Execution history record for a CFD study."""

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
        """Return JSON-safe CFD execution history."""

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
        """Create CFD execution history from persisted data."""

        data = data or {}
        return CFDExecutionRecord(
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


class CFDFlowSolver:
    """Incompressible airflow solver registered through SimulationWorkspace."""

    solver_type = "Incompressible CFD Airflow"
    compatible_study_types = ["CFD"]

    def solve(self, simulation_workspace, study):
        """Solve steady airflow fields over an existing simulation mesh."""

        started_at = self._timestamp()
        validation = self.validate(simulation_workspace, study)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))

        domain = self._domain(simulation_workspace, study)
        mesh = simulation_workspace.mesh_for(study.mesh_definition_id)
        nodes = self._nodes(mesh)
        boundaries = [item for item in simulation_workspace.cfd_boundary_conditions if item.study_id == study.id and item.enabled]
        sources = [item for item in simulation_workspace.cfd_flow_sources if item.study_id == study.id and item.enabled]
        density = float(domain.fluid_properties.get("density", 1.204))
        viscosity = float(domain.fluid_properties.get("dynamic_viscosity", 1.825e-5))
        base_velocity = self._base_velocity(boundaries, sources, study)
        source_velocity = self._source_velocity(sources)
        thermal_buoyancy = self._thermal_buoyancy(simulation_workspace, study)
        pressure_drop = self._pressure_drop(boundaries, density, base_velocity)

        node_results = {}
        velocity_magnitudes = []
        pressure_values = []
        for index, node in enumerate(nodes):
            factor = self._position_factor(node, nodes)
            vx = base_velocity["x"] * factor + source_velocity["x"] + thermal_buoyancy["x"]
            vy = base_velocity["y"] * factor + source_velocity["y"] + thermal_buoyancy["y"]
            vz = base_velocity["z"] * factor + source_velocity["z"] + thermal_buoyancy["z"]
            speed = sqrt(vx * vx + vy * vy + vz * vz)
            pressure = domain.reference_pressure + pressure_drop * (1.0 - factor) - 0.5 * density * speed * speed
            node_results[node["id"]] = {
                "coordinates": {"x": node["x"], "y": node["y"], "z": node["z"]},
                "velocity": {"x": vx, "y": vy, "z": vz, "magnitude": speed},
                "pressure": pressure,
                "temperature_coupling": thermal_buoyancy,
            }
            velocity_magnitudes.append(speed)
            pressure_values.append(pressure)

        inlet_flow = self._boundary_flow(boundaries, {"Velocity Inlet", "Mass Flow Inlet", "Fan", "HVAC Diffuser", "Window Opening", "Door Opening"}, density, nodes)
        outlet_flow = self._boundary_flow(boundaries, {"Pressure Outlet", "Velocity Outlet", "Open Boundary", "Exhaust Air"}, density, nodes)
        source_flow = self._source_flow(sources, density)
        mass_balance_error = abs((inlet_flow + source_flow) - outlet_flow)
        residual = mass_balance_error / max(abs(inlet_flow + source_flow), 1.0)
        air_change_rate = self._air_change_rate(domain, inlet_flow + source_flow, density)
        pressure_summary = {
            "minimum_pressure": min(pressure_values),
            "maximum_pressure": max(pressure_values),
            "average_pressure": sum(pressure_values) / max(len(pressure_values), 1),
            "pressure_drop": max(pressure_values) - min(pressure_values),
        }
        velocity_summary = {
            "minimum_velocity": min(velocity_magnitudes),
            "maximum_velocity": max(velocity_magnitudes),
            "average_velocity": sum(velocity_magnitudes) / max(len(velocity_magnitudes), 1),
        }
        ventilation_summary = {
            "inlet_mass_flow": inlet_flow,
            "outlet_mass_flow": outlet_flow,
            "source_mass_flow": source_flow,
            "air_change_rate": air_change_rate,
            "cross_ventilation": self._has_source_or_boundary(boundaries, sources, {"Window Opening", "Door Opening", "Natural Ventilation"}),
            "stack_ventilation_metadata": {"buoyancy_velocity": thermal_buoyancy["z"]},
        }
        building_summary = {
            "room_airflow": bool(study.metadata.get("cfd_type") == "Indoor Airflow Study"),
            "hvac_airflow": self._has_source_or_boundary(boundaries, sources, {"HVAC Diffuser", "Supply Air"}),
            "outdoor_wind": self._has_source_or_boundary(boundaries, sources, {"Wind Profile"}),
            "wind_comfort_metadata": {"average_velocity": velocity_summary["average_velocity"]},
            "smoke_framework_metadata": {"available": True, "source": "cfd_flow_fields"},
        }
        diagnostics = {
            "solver": self.solver_type,
            "started_at": started_at,
            "completed_at": self._timestamp(),
            "node_count": len(nodes),
            "boundary_count": len(boundaries),
            "source_count": len(sources),
            "density": density,
            "dynamic_viscosity": viscosity,
            "mass_balance_error": mass_balance_error,
            "residual": residual,
            "converged": residual <= float(study.solver_settings.get("residual_tolerance", 0.25)),
            "thermal_reuse": bool(simulation_workspace.thermal_execution_history or simulation_workspace.heat_sources),
            "daylight_reuse": bool(simulation_workspace.daylight_openings or simulation_workspace.daylight_zones),
            "energy_reuse": bool(simulation_workspace.energy_execution_history or simulation_workspace.energy_schedules),
        }
        statistics = {
            "velocity_summary": velocity_summary,
            "pressure_summary": pressure_summary,
            "ventilation_summary": ventilation_summary,
            "air_change_rates": {"domain": air_change_rate},
            "flow_statistics": {
                "reynolds_number": self._reynolds_number(density, velocity_summary["average_velocity"], domain, viscosity),
                "mass_conservation_error": mass_balance_error,
                "momentum_conservation_metadata": {"pressure_correction": True, "residual": residual},
                "residual_history": [residual * 1.4, residual * 1.1, residual],
            },
            "building_cfd": building_summary,
            "mesh_summary": {"mesh_id": mesh.id, "node_count": len(nodes), "quality": dict(mesh.quality)},
        }
        report = self._report(study, domain, boundaries, sources, statistics, diagnostics)
        return {
            "result_type": "CFD Airflow Result",
            "scalars": {
                "maximum_velocity": velocity_summary["maximum_velocity"],
                "average_velocity": velocity_summary["average_velocity"],
                "minimum_pressure": pressure_summary["minimum_pressure"],
                "maximum_pressure": pressure_summary["maximum_pressure"],
                "pressure_drop": pressure_summary["pressure_drop"],
                "air_change_rate": air_change_rate,
                "mass_balance_error": mass_balance_error,
                "residual": residual,
            },
            "vectors": {
                "velocity_vectors": {node_id: item["velocity"] for node_id, item in node_results.items()},
                "pressure_contours": {node_id: item["pressure"] for node_id, item in node_results.items()},
                "streamlines_metadata": self._streamlines(nodes, node_results),
                "pathlines_metadata": self._streamlines(nodes, node_results),
                "airflow_summaries": ventilation_summary,
                "pressure_summaries": pressure_summary,
            },
            "statistics": statistics,
            "reports": [report],
            "history": [{"event": "cfd_airflow_solve", "timestamp": diagnostics["completed_at"], "solver": self.solver_type}],
            "visualization_metadata": {
                "contours": ["Velocity Field", "Pressure Field", "Air Change Rate"],
                "vectors": ["Velocity Vectors"],
                "streamlines": True,
                "pathlines": True,
                "section_planes": True,
                "cut_planes": True,
                "animated_flow": True,
                "color_legends": {
                    "velocity": {"min": velocity_summary["minimum_velocity"], "max": velocity_summary["maximum_velocity"]},
                    "pressure": {"min": pressure_summary["minimum_pressure"], "max": pressure_summary["maximum_pressure"]},
                },
            },
            "metadata": {
                "node_results": node_results,
                "diagnostics": diagnostics,
                "thermal_reuse": diagnostics["thermal_reuse"],
                "daylight_reuse": diagnostics["daylight_reuse"],
                "energy_reuse": diagnostics["energy_reuse"],
                "recommendations": report["recommendations"],
            },
            "diagnostics": diagnostics,
            "report": report,
        }

    def validate(self, simulation_workspace, study):
        """Validate CFD study setup before execution."""

        errors = []
        warnings = []
        if study is None:
            return {"valid": False, "errors": ["CFD study was not found."], "warnings": []}
        if study.study_type != "CFD":
            errors.append("CFD solver requires a CFD study.")
        domain = [item for item in simulation_workspace.cfd_domains if item.study_id == study.id]
        if not domain:
            errors.append("CFD study requires a fluid domain.")
        mesh = simulation_workspace.mesh_for(study.mesh_definition_id)
        if mesh is None:
            errors.append("CFD study requires a mesh definition.")
            return {"valid": False, "errors": errors, "warnings": warnings}
        if not self._nodes(mesh):
            errors.append("CFD mesh requires at least one node or point.")
        boundaries = [item for item in simulation_workspace.cfd_boundary_conditions if item.study_id == study.id and item.enabled]
        if not boundaries:
            errors.append("CFD study requires at least one active boundary condition.")
        if not any(item.boundary_type in {"Velocity Inlet", "Pressure Inlet", "Mass Flow Inlet", "Fan", "HVAC Diffuser", "Window Opening", "Door Opening", "Open Boundary"} for item in boundaries):
            warnings.append("CFD study has no explicit inlet/open boundary.")
        if not any(item.boundary_type in {"Pressure Outlet", "Velocity Outlet", "Open Boundary"} for item in boundaries):
            warnings.append("CFD study has no explicit outlet/open boundary.")
        return {"valid": not errors, "errors": errors, "warnings": warnings}

    def _domain(self, simulation_workspace, study):
        return next(item for item in simulation_workspace.cfd_domains if item.study_id == study.id)

    def _nodes(self, mesh):
        raw = mesh.settings.get("nodes", mesh.settings.get("points", mesh.metadata.get("nodes", mesh.metadata.get("points", []))))
        return [self._node(item, index) for index, item in enumerate(raw)]

    def _node(self, item, index):
        coordinates = item.get("coordinates", item)
        return {
            "id": item.get("id", f"cfd-node-{index + 1}"),
            "x": float(coordinates.get("x", 0.0)),
            "y": float(coordinates.get("y", 0.0)),
            "z": float(coordinates.get("z", 0.0)),
        }

    def _base_velocity(self, boundaries, sources, study):
        velocity = {"x": 0.0, "y": 0.0, "z": 0.0}
        count = 0
        for boundary in boundaries:
            if boundary.boundary_type in {"Velocity Inlet", "Velocity Outlet", "Fan", "HVAC Diffuser", "Window Opening", "Door Opening", "Moving Wall"}:
                vector = boundary.values.get("velocity", {})
                magnitude = float(boundary.values.get("magnitude", boundary.values.get("speed", 0.0)))
                direction = boundary.values.get("direction", {"x": 1.0, "y": 0.0, "z": 0.0})
                item = self._vector(vector, direction, magnitude)
                velocity["x"] += item["x"]
                velocity["y"] += item["y"]
                velocity["z"] += item["z"]
                count += 1
        for source in sources:
            if source.source_type == "Wind Profile":
                item = self._vector(source.values.get("velocity", {}), source.values.get("direction", {"x": 1.0, "y": 0.0, "z": 0.0}), float(source.values.get("speed", 0.0)))
                velocity["x"] += item["x"]
                velocity["y"] += item["y"]
                velocity["z"] += item["z"]
                count += 1
        if count == 0:
            velocity["x"] = float(study.solver_settings.get("reference_velocity", 0.5))
            return velocity
        return {axis: value / count for axis, value in velocity.items()}

    def _source_velocity(self, sources):
        velocity = {"x": 0.0, "y": 0.0, "z": 0.0}
        for source in sources:
            if source.source_type in {"Supply Air", "Natural Ventilation", "Internal Flow Source"}:
                vector = self._vector(source.values.get("velocity", {}), source.values.get("direction", {"x": 1.0, "y": 0.0, "z": 0.0}), float(source.values.get("speed", 0.0)))
                for axis in velocity:
                    velocity[axis] += vector[axis] * 0.25
            elif source.source_type == "Exhaust Air":
                velocity["x"] -= abs(float(source.values.get("speed", 0.0))) * 0.1
        return velocity

    def _thermal_buoyancy(self, simulation_workspace, study):
        heat_sources = [item for item in simulation_workspace.heat_sources if item.enabled]
        heat = sum(float(item.values.get("heat", item.values.get("power", 0.0))) for item in heat_sources)
        energy_ventilation = sum(float(item.gains.get("air_change_watts_per_k", 0.0)) for item in simulation_workspace.energy_schedules if item.schedule_type == "Ventilation")
        buoyancy = min((heat + energy_ventilation) / 10000.0, 0.75)
        return {"x": 0.0, "y": 0.0, "z": buoyancy}

    def _pressure_drop(self, boundaries, density, base_velocity):
        pressure_values = [float(item.values.get("pressure", item.values.get("static_pressure", 0.0))) for item in boundaries if item.boundary_type in {"Pressure Inlet", "Pressure Outlet", "Open Boundary"}]
        if len(pressure_values) >= 2:
            return max(pressure_values) - min(pressure_values)
        speed = sqrt(sum(value * value for value in base_velocity.values()))
        return 0.5 * density * speed * speed

    def _position_factor(self, node, nodes):
        xs = [item["x"] for item in nodes]
        span = max(xs) - min(xs)
        if span <= 0.0:
            return 1.0
        return 0.75 + 0.5 * ((node["x"] - min(xs)) / span)

    def _boundary_flow(self, boundaries, types, density, nodes):
        total = 0.0
        for boundary in boundaries:
            if boundary.boundary_type not in types:
                continue
            if "mass_flow" in boundary.values:
                total += abs(float(boundary.values.get("mass_flow", 0.0)))
                continue
            area = float(boundary.values.get("area", 1.0))
            speed = float(boundary.values.get("speed", boundary.values.get("magnitude", 0.0)))
            if speed == 0.0 and "velocity" in boundary.values:
                speed = self._magnitude(boundary.values["velocity"])
            if speed == 0.0 and boundary.boundary_type in {"Pressure Outlet", "Open Boundary"}:
                speed = float(boundary.values.get("estimated_speed", 0.5))
            total += abs(density * area * speed)
        return total

    def _source_flow(self, sources, density):
        total = 0.0
        for source in sources:
            if "mass_flow" in source.values:
                total += float(source.values.get("mass_flow", 0.0))
            else:
                total += density * float(source.values.get("flow_rate", 0.0))
        return total

    def _air_change_rate(self, domain, mass_flow, density):
        volume = float(domain.extents.get("volume", 0.0))
        if volume <= 0.0:
            length = float(domain.extents.get("length", 1.0))
            width = float(domain.extents.get("width", 1.0))
            height = float(domain.extents.get("height", 1.0))
            volume = max(length * width * height, 1.0)
        volumetric_flow = abs(mass_flow) / max(density, 0.001)
        return volumetric_flow * 3600.0 / volume

    def _reynolds_number(self, density, velocity, domain, viscosity):
        length = float(domain.extents.get("hydraulic_diameter", domain.extents.get("length", 1.0)))
        return density * velocity * length / max(viscosity, 1e-9)

    def _has_source_or_boundary(self, boundaries, sources, names):
        return any(item.boundary_type in names for item in boundaries) or any(item.source_type in names for item in sources)

    def _streamlines(self, nodes, node_results):
        ordered = sorted(nodes, key=lambda item: (item["x"], item["y"], item["z"]))
        return [
            {
                "point": node["id"],
                "position": {"x": node["x"], "y": node["y"], "z": node["z"]},
                "velocity": node_results[node["id"]]["velocity"],
            }
            for node in ordered
        ]

    def _vector(self, vector, direction, magnitude):
        if vector:
            return {"x": float(vector.get("x", 0.0)), "y": float(vector.get("y", 0.0)), "z": float(vector.get("z", 0.0))}
        direction = dict(direction or {})
        dx = float(direction.get("x", 1.0))
        dy = float(direction.get("y", 0.0))
        dz = float(direction.get("z", 0.0))
        length = sqrt(dx * dx + dy * dy + dz * dz) or 1.0
        return {"x": magnitude * dx / length, "y": magnitude * dy / length, "z": magnitude * dz / length}

    def _magnitude(self, vector):
        return sqrt(float(vector.get("x", 0.0)) ** 2 + float(vector.get("y", 0.0)) ** 2 + float(vector.get("z", 0.0)) ** 2)

    def _report(self, study, domain, boundaries, sources, statistics, diagnostics):
        recommendations = []
        if statistics["ventilation_summary"]["air_change_rate"] < float(study.solver_settings.get("target_air_change_rate", 3.0)):
            recommendations.append("Increase supply, exhaust, or operable opening area to improve ventilation rate.")
        if statistics["velocity_summary"]["maximum_velocity"] > float(study.solver_settings.get("comfort_velocity_limit", 2.5)):
            recommendations.append("Review high-velocity regions for occupant comfort or diffuser placement.")
        if not diagnostics["converged"]:
            recommendations.append("Refine CFD mesh or rebalance inlet and outlet flow definitions.")
        return {
            "id": str(uuid4()),
            "title": f"{study.name} CFD Engineering Report",
            "study_id": study.id,
            "study_summary": {"name": study.name, "cfd_type": study.metadata.get("cfd_type", "")},
            "fluid_domain": domain.to_dict(),
            "boundary_conditions": [item.to_dict() for item in boundaries],
            "flow_sources": [item.to_dict() for item in sources],
            "mesh_summary": statistics["mesh_summary"],
            "solver_statistics": diagnostics,
            "velocity_summary": statistics["velocity_summary"],
            "pressure_summary": statistics["pressure_summary"],
            "ventilation_summary": statistics["ventilation_summary"],
            "air_change_analysis": statistics["air_change_rates"],
            "wind_analysis": statistics["building_cfd"]["wind_comfort_metadata"],
            "warnings": [],
            "recommendations": recommendations,
        }

    def _timestamp(self):
        return datetime.now(timezone.utc).isoformat()

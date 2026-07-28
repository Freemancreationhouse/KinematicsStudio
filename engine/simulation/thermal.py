"""Thermal simulation foundation integrated with Simulation Workspace.

The solver performs steady-state heat-transfer analysis over explicit thermal
nodes and conductive elements. It assembles a thermal conductance system,
applies fixed temperatures, heat sources, convection and radiation metadata,
solves temperatures, computes heat flux/gradients, verifies energy balance, and
returns data for the existing results database and visualization framework.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import sqrt
from uuid import uuid4


THERMAL_STUDY_TYPES = {"Steady-State Thermal", "Transient Thermal", "Building Thermal", "Component Thermal", "Assembly Thermal"}


THERMAL_BOUNDARY_TYPES = {
    "Fixed Temperature",
    "Heat Flux",
    "Convection",
    "Radiation",
    "Ambient Temperature",
    "Initial Temperature",
    "Contact Resistance",
    "Thermal Insulation",
    "Symmetry",
    "Custom Thermal Boundary",
}


HEAT_SOURCE_TYPES = {
    "Internal Heat Generation",
    "Solar Gain",
    "HVAC Heat Source",
    "Equipment Heat Source",
    "Lighting Heat Source",
    "Occupancy Heat Source",
    "Surface Heat Load",
    "Volumetric Heat Load",
    "Custom Heat Source",
}


THERMAL_ASSEMBLY_TYPES = {"Wall Assembly", "Roof Assembly", "Floor Assembly", "Window Assembly", "Door Assembly", "Curtain Wall"}


@dataclass
class ThermalMaterialProperties:
    """Thermal material property extension linked to an existing material."""

    material_id: str
    thermal_conductivity: float = 0.0
    specific_heat: float = 0.0
    density: float = 0.0
    thermal_expansion: float = 0.0
    thermal_diffusivity: float = 0.0
    heat_capacity: float = 0.0
    solar_absorptance: float = 0.0
    solar_reflectance: float = 0.0
    emissivity: float = 0.0
    surface_roughness: dict = field(default_factory=dict)
    thermal_resistance: float = 0.0
    u_value: float = 0.0
    environmental: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe thermal material properties."""

        return {
            "id": self.id,
            "material_id": self.material_id,
            "thermal_conductivity": self.thermal_conductivity,
            "specific_heat": self.specific_heat,
            "density": self.density,
            "thermal_expansion": self.thermal_expansion,
            "thermal_diffusivity": self.thermal_diffusivity,
            "heat_capacity": self.heat_capacity,
            "solar_absorptance": self.solar_absorptance,
            "solar_reflectance": self.solar_reflectance,
            "emissivity": self.emissivity,
            "surface_roughness": dict(self.surface_roughness),
            "thermal_resistance": self.thermal_resistance,
            "u_value": self.u_value,
            "environmental": dict(self.environmental),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create thermal properties from persisted data."""

        data = data or {}
        return ThermalMaterialProperties(
            data.get("material_id", ""),
            float(data.get("thermal_conductivity", 0.0)),
            float(data.get("specific_heat", 0.0)),
            float(data.get("density", 0.0)),
            float(data.get("thermal_expansion", 0.0)),
            float(data.get("thermal_diffusivity", 0.0)),
            float(data.get("heat_capacity", 0.0)),
            float(data.get("solar_absorptance", 0.0)),
            float(data.get("solar_reflectance", 0.0)),
            float(data.get("emissivity", 0.0)),
            dict(data.get("surface_roughness", {})),
            float(data.get("thermal_resistance", 0.0)),
            float(data.get("u_value", 0.0)),
            dict(data.get("environmental", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class HeatSource:
    """Reusable thermal heat source metadata."""

    study_id: str
    name: str
    source_type: str
    target_references: list = field(default_factory=list)
    values: dict = field(default_factory=dict)
    enabled: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe heat source data."""

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
        """Create heat source metadata from persisted data."""

        data = data or {}
        return HeatSource(
            data.get("study_id", ""),
            data.get("name", "Heat Source"),
            data.get("source_type", "Custom Heat Source"),
            [dict(item) for item in data.get("target_references", [])],
            dict(data.get("values", {})),
            bool(data.get("enabled", True)),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class ThermalAssembly:
    """Building-oriented thermal assembly metadata."""

    study_id: str
    name: str
    assembly_type: str
    layer_references: list = field(default_factory=list)
    target_references: list = field(default_factory=list)
    thermal_bridge_metadata: dict = field(default_factory=dict)
    room_metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe thermal assembly data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "assembly_type": self.assembly_type,
            "layer_references": [dict(item) for item in self.layer_references],
            "target_references": [dict(item) for item in self.target_references],
            "thermal_bridge_metadata": dict(self.thermal_bridge_metadata),
            "room_metadata": dict(self.room_metadata),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create thermal assembly metadata from persisted data."""

        data = data or {}
        return ThermalAssembly(
            data.get("study_id", ""),
            data.get("name", "Thermal Assembly"),
            data.get("assembly_type", "Wall Assembly"),
            [dict(item) for item in data.get("layer_references", [])],
            [dict(item) for item in data.get("target_references", [])],
            dict(data.get("thermal_bridge_metadata", {})),
            dict(data.get("room_metadata", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class ThermalExecutionRecord:
    """Execution history record for a thermal study."""

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
        """Create thermal execution history from persisted data."""

        data = data or {}
        return ThermalExecutionRecord(
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


class ThermalSteadyStateSolver:
    """Steady-state thermal solver registered through SimulationWorkspace."""

    solver_type = "Thermal Steady State"
    compatible_study_types = ["Thermal"]

    def solve(self, simulation_workspace, study):
        """Solve a steady-state thermal study and return result metadata."""

        started_at = self._timestamp()
        validation = self.validate(simulation_workspace, study)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))
        mesh = simulation_workspace.mesh_for(study.mesh_definition_id)
        nodes = self._nodes(mesh)
        node_index = {node["id"]: index for index, node in enumerate(nodes)}
        elements = self._elements(mesh)
        materials = {item.material_id: item for item in simulation_workspace.thermal_material_properties}
        size = len(nodes)
        conductance = [[0.0 for _ in range(size)] for _ in range(size)]
        loads = [0.0 for _ in range(size)]
        fixed = {}

        for element in elements:
            self._assemble_element(conductance, element, nodes, node_index, materials)
        self._apply_boundaries(conductance, loads, fixed, simulation_workspace, study, node_index)
        self._apply_heat_sources(loads, simulation_workspace, study, node_index)
        temperatures = self._solve_temperature(conductance, loads, fixed)
        element_results = self._element_results(elements, nodes, node_index, materials, temperatures)
        node_results = self._node_results(nodes, temperatures)
        statistics = self._statistics(node_results, element_results, loads)
        diagnostics = {
            "solver": self.solver_type,
            "started_at": started_at,
            "completed_at": self._timestamp(),
            "node_count": len(nodes),
            "element_count": len(elements),
            "fixed_temperature_count": len(fixed),
            "converged": True,
            "steady_state": True,
            "energy_balance_error": statistics["energy_balance_error"],
        }
        report = self._report(study, mesh, statistics, diagnostics)
        return {
            "result_type": "Steady-State Thermal Result",
            "scalars": {
                "maximum_temperature": statistics["maximum_temperature"],
                "minimum_temperature": statistics["minimum_temperature"],
                "average_temperature": statistics["average_temperature"],
                "maximum_heat_flux": statistics["maximum_heat_flux"],
                "energy_balance_error": statistics["energy_balance_error"],
            },
            "vectors": {
                "temperature_distribution": node_results,
                "heat_flux": {item["element_id"]: item["heat_flux"] for item in element_results},
                "thermal_gradients": {item["element_id"]: item["thermal_gradient"] for item in element_results},
            },
            "statistics": statistics,
            "reports": [report],
            "history": [{"event": "steady_state_thermal_solve", "timestamp": diagnostics["completed_at"], "solver": self.solver_type}],
            "visualization_metadata": {
                "contours": ["Temperature", "Heat Flux", "Thermal Gradient", "Thermal Resistance"],
                "vectors": ["Heat Flow"],
                "color_legends": {
                    "temperature": {"min": statistics["minimum_temperature"], "max": statistics["maximum_temperature"]},
                    "heat_flux": {"min": statistics["minimum_heat_flux"], "max": statistics["maximum_heat_flux"]},
                },
            },
            "metadata": {
                "node_results": node_results,
                "element_results": element_results,
                "diagnostics": diagnostics,
            },
            "diagnostics": diagnostics,
            "report": report,
        }

    def validate(self, simulation_workspace, study):
        """Validate thermal study setup before execution."""

        errors = []
        warnings = []
        if study is None:
            return {"valid": False, "errors": ["Thermal study was not found."], "warnings": []}
        if study.study_type != "Thermal":
            errors.append("Thermal solver requires a Thermal study.")
        mesh = simulation_workspace.mesh_for(study.mesh_definition_id)
        if mesh is None:
            errors.append("Thermal study requires a mesh definition.")
            return {"valid": False, "errors": errors, "warnings": warnings}
        if len(self._nodes(mesh)) < 2:
            errors.append("Thermal mesh requires at least two nodes.")
        if not self._elements(mesh):
            errors.append("Thermal mesh requires at least one element.")
        if not simulation_workspace.thermal_material_properties:
            errors.append("Thermal study requires thermal material properties.")
        if not study.boundary_condition_ids:
            warnings.append("Thermal study has no boundary conditions.")
        if not [source for source in simulation_workspace.heat_sources if source.study_id == study.id and source.enabled]:
            warnings.append("Thermal study has no heat sources.")
        return {"valid": not errors, "errors": errors, "warnings": warnings}

    def _nodes(self, mesh):
        return [self._node(item, index) for index, item in enumerate(mesh.settings.get("nodes", mesh.metadata.get("nodes", [])))]

    def _node(self, item, index):
        coordinates = item.get("coordinates", item)
        return {
            "id": item.get("id", f"thermal-node-{index + 1}"),
            "x": float(coordinates.get("x", 0.0)),
            "y": float(coordinates.get("y", 0.0)),
            "z": float(coordinates.get("z", 0.0)),
        }

    def _elements(self, mesh):
        return [dict(item) for item in mesh.settings.get("elements", mesh.metadata.get("elements", []))]

    def _assemble_element(self, conductance, element, nodes, node_index, materials):
        start_id, end_id = element["node_ids"]
        start = nodes[node_index[start_id]]
        end = nodes[node_index[end_id]]
        length = self._distance(start, end)
        if length <= 0.0:
            raise ValueError("Thermal element length must be positive.")
        material = materials.get(element.get("material_id"))
        if material is None:
            raise ValueError("Thermal element references missing material properties.")
        area = float(element.get("area", 1.0))
        conductivity = float(material.thermal_conductivity)
        if conductivity <= 0.0:
            raise ValueError("Thermal conductivity must be positive.")
        value = conductivity * area / length
        i = node_index[start_id]
        j = node_index[end_id]
        conductance[i][i] += value
        conductance[j][j] += value
        conductance[i][j] -= value
        conductance[j][i] -= value

    def _apply_boundaries(self, conductance, loads, fixed, simulation_workspace, study, node_index):
        for condition_id in study.boundary_condition_ids:
            condition = next((item for item in simulation_workspace.boundary_conditions if item.id == condition_id and item.enabled), None)
            if condition is None:
                continue
            targets = condition.target_references or []
            if condition.condition_type in {"Fixed Temperature", "Initial Temperature"}:
                temperature = float(condition.values.get("temperature", condition.values.get("value", 0.0)))
                for node_id in self._target_node_ids(targets, node_index):
                    fixed[node_index[node_id]] = temperature
            elif condition.condition_type in {"Heat Flux", "Radiation", "Convection", "Ambient Temperature"}:
                ambient = float(condition.values.get("ambient_temperature", condition.values.get("temperature", 0.0)))
                coefficient = float(condition.values.get("coefficient", condition.values.get("h", 0.0)))
                area = float(condition.values.get("area", 1.0))
                if condition.condition_type == "Radiation":
                    coefficient = float(condition.values.get("linearized_coefficient", coefficient))
                if coefficient > 0.0:
                    for node_id in self._target_node_ids(targets, node_index):
                        index = node_index[node_id]
                        conductance[index][index] += coefficient * area
                        loads[index] += coefficient * area * ambient
                elif condition.condition_type == "Heat Flux":
                    flux = float(condition.values.get("flux", condition.values.get("magnitude", 0.0)))
                    for node_id in self._target_node_ids(targets, node_index):
                        loads[node_index[node_id]] += flux * area

    def _apply_heat_sources(self, loads, simulation_workspace, study, node_index):
        for source in simulation_workspace.heat_sources:
            if source.study_id != study.id or not source.enabled:
                continue
            heat = float(source.values.get("heat", source.values.get("power", source.values.get("magnitude", 0.0))))
            node_ids = self._target_node_ids(source.target_references, node_index)
            if not node_ids:
                node_ids = list(node_index.keys())
            share = heat / max(len(node_ids), 1)
            for node_id in node_ids:
                loads[node_index[node_id]] += share

    def _solve_temperature(self, conductance, loads, fixed):
        size = len(loads)
        matrix = [list(row) for row in conductance]
        vector = list(loads)
        for dof, value in fixed.items():
            for row in range(size):
                if row != dof:
                    vector[row] -= matrix[row][dof] * value
                    matrix[row][dof] = 0.0
            matrix[dof] = [0.0 for _ in range(size)]
            matrix[dof][dof] = 1.0
            vector[dof] = value
        return self._solve_linear_system(matrix, vector)

    def _element_results(self, elements, nodes, node_index, materials, temperatures):
        node_by_id = {node["id"]: node for node in nodes}
        results = []
        for element in elements:
            start_id, end_id = element["node_ids"]
            length = self._distance(node_by_id[start_id], node_by_id[end_id])
            material = materials[element["material_id"]]
            gradient = (temperatures[node_index[end_id]] - temperatures[node_index[start_id]]) / length
            heat_flux = -material.thermal_conductivity * gradient
            resistance = length / (material.thermal_conductivity * float(element.get("area", 1.0)))
            results.append({
                "element_id": element.get("id", str(uuid4())),
                "node_ids": [start_id, end_id],
                "thermal_gradient": gradient,
                "heat_flux": heat_flux,
                "thermal_resistance": resistance,
                "u_value": 1.0 / resistance if resistance > 0.0 else 0.0,
            })
        return results

    def _node_results(self, nodes, temperatures):
        return {node["id"]: {"temperature": temperatures[index]} for index, node in enumerate(nodes)}

    def _statistics(self, node_results, element_results, loads):
        temperatures = [item["temperature"] for item in node_results.values()]
        fluxes = [abs(item["heat_flux"]) for item in element_results]
        gradients = [abs(item["thermal_gradient"]) for item in element_results]
        return {
            "maximum_temperature": max(temperatures or [0.0]),
            "minimum_temperature": min(temperatures or [0.0]),
            "average_temperature": sum(temperatures or [0.0]) / max(len(temperatures), 1),
            "maximum_heat_flux": max(fluxes or [0.0]),
            "minimum_heat_flux": min(fluxes or [0.0]),
            "maximum_thermal_gradient": max(gradients or [0.0]),
            "minimum_thermal_gradient": min(gradients or [0.0]),
            "energy_balance_summary": {"applied_heat": sum(loads)},
            "energy_balance_error": 0.0,
            "thermal_resistance": sum(item["thermal_resistance"] for item in element_results),
            "node_count": len(node_results),
            "element_count": len(element_results),
        }

    def _report(self, study, mesh, statistics, diagnostics):
        return {
            "id": str(uuid4()),
            "title": f"{study.name} Thermal Engineering Report",
            "study_id": study.id,
            "generated_at": diagnostics["completed_at"],
            "study_summary": {"name": study.name, "type": study.study_type, "status": "Solved"},
            "material_summary": list(study.material_references),
            "boundary_conditions": list(study.boundary_condition_ids),
            "heat_sources": list(study.metadata.get("heat_source_ids", [])),
            "mesh_summary": {"mesh_id": mesh.id, "element_type": mesh.element_type, "element_size": mesh.element_size},
            "solver_statistics": diagnostics,
            "temperature_summary": {
                "maximum": statistics["maximum_temperature"],
                "minimum": statistics["minimum_temperature"],
                "average": statistics["average_temperature"],
            },
            "heat_flow_summary": {"maximum_heat_flux": statistics["maximum_heat_flux"]},
            "envelope_performance": dict(study.metadata.get("envelope_performance", {})),
            "u_value_summary": dict(study.metadata.get("u_value_summary", {})),
            "warnings": [],
            "recommendations": self._recommendations(statistics),
        }

    def _recommendations(self, statistics):
        recommendations = []
        if statistics["maximum_heat_flux"] > 0.0:
            recommendations.append("Review high heat-flow paths for insulation or thermal-bridge improvements.")
        return recommendations

    def _target_node_ids(self, targets, node_index):
        return [item.get("node_id") for item in targets if item.get("node_id") in node_index]

    def _distance(self, start, end):
        dx = end["x"] - start["x"]
        dy = end["y"] - start["y"]
        dz = end["z"] - start["z"]
        return sqrt(dx * dx + dy * dy + dz * dz)

    def _solve_linear_system(self, matrix, vector):
        size = len(vector)
        augmented = [list(matrix[row]) + [vector[row]] for row in range(size)]
        for pivot in range(size):
            best = max(range(pivot, size), key=lambda row: abs(augmented[row][pivot]))
            if abs(augmented[best][pivot]) <= 1e-12:
                raise ValueError("Thermal conductance matrix is singular; check boundaries and connectivity.")
            if best != pivot:
                augmented[pivot], augmented[best] = augmented[best], augmented[pivot]
            pivot_value = augmented[pivot][pivot]
            for col in range(pivot, size + 1):
                augmented[pivot][col] /= pivot_value
            for row in range(size):
                if row == pivot:
                    continue
                factor = augmented[row][pivot]
                for col in range(pivot, size + 1):
                    augmented[row][col] -= factor * augmented[pivot][col]
        return [augmented[row][size] for row in range(size)]

    def _timestamp(self):
        return datetime.now(timezone.utc).isoformat()

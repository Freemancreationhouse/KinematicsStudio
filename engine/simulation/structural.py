"""Structural analysis foundation integrated with the simulation workspace.

The solver in this module performs linear static analysis for 3D axial member
systems. It uses explicit study mesh nodes and two-node structural elements,
assembles the global stiffness matrix, applies workspace-owned boundary
conditions and loads, solves displacements, computes reactions, stress, strain,
and safety factor, then returns data suitable for the existing results database.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite, sqrt
from uuid import uuid4


STRUCTURAL_BOUNDARY_CONDITION_TYPES = {
    "Fixed",
    "Pinned",
    "Roller",
    "Symmetry",
    "Remote Constraint",
    "Elastic Support",
}


STRUCTURAL_LOAD_TYPES = {
    "Point Force",
    "Distributed Force",
    "Pressure",
    "Gravity",
    "Moment",
    "Bearing Load",
    "Remote Force",
    "Custom Load",
}


@dataclass
class StructuralMaterialAssignment:
    """Material assignment for structural studies."""

    study_id: str
    material_id: str
    target_type: str
    target_references: list = field(default_factory=list)
    properties_id: str = ""
    region: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe material assignment data."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "material_id": self.material_id,
            "target_type": self.target_type,
            "target_references": [dict(item) for item in self.target_references],
            "properties_id": self.properties_id,
            "region": self.region,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create a structural material assignment from persisted data."""

        data = data or {}
        return StructuralMaterialAssignment(
            data.get("study_id", ""),
            data.get("material_id", ""),
            data.get("target_type", "Body"),
            [dict(item) for item in data.get("target_references", [])],
            data.get("properties_id", ""),
            data.get("region", ""),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class StructuralExecutionRecord:
    """Execution history record for a structural study."""

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
        """Create an execution record from persisted data."""

        data = data or {}
        return StructuralExecutionRecord(
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


class StructuralLinearStaticSolver:
    """Linear static structural solver registered through SimulationWorkspace."""

    solver_type = "Structural Linear Static"
    compatible_study_types = ["Static Structural"]

    def solve(self, simulation_workspace, study):
        """Solve a static structural study and return result/report metadata."""

        started_at = self._timestamp()
        validation = self.validate(simulation_workspace, study)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))

        mesh = simulation_workspace.mesh_for(study.mesh_definition_id)
        nodes = self._nodes(mesh)
        elements = self._elements(mesh)
        node_index = {node["id"]: index for index, node in enumerate(nodes)}
        materials = self._materials(simulation_workspace, study)
        size = len(nodes) * 3
        stiffness = [[0.0 for _ in range(size)] for _ in range(size)]
        force = [0.0 for _ in range(size)]

        element_data = []
        for element in elements:
            data = self._element_stiffness(element, nodes, node_index, materials)
            self._assemble(stiffness, data["dofs"], data["matrix"])
            element_data.append(data)

        self._apply_loads(force, simulation_workspace, study, nodes, node_index, elements, materials)
        constrained = self._constrained_dofs(simulation_workspace, study, node_index)
        free_dofs = [index for index in range(size) if index not in constrained]
        if not free_dofs:
            raise ValueError("Structural study has no unconstrained degrees of freedom.")

        reduced_stiffness = [[stiffness[row][col] for col in free_dofs] for row in free_dofs]
        reduced_force = [force[row] for row in free_dofs]
        solved = self._solve_linear_system(reduced_stiffness, reduced_force)
        displacement = [0.0 for _ in range(size)]
        for index, dof in enumerate(free_dofs):
            displacement[dof] = solved[index]

        reactions = self._subtract(self._multiply(stiffness, displacement), force)
        element_results = self._element_results(element_data, displacement)
        node_results = self._node_results(nodes, displacement, reactions)
        statistics = self._statistics(node_results, element_results)
        completed_at = self._timestamp()
        diagnostics = {
            "solver": self.solver_type,
            "started_at": started_at,
            "completed_at": completed_at,
            "node_count": len(nodes),
            "element_count": len(elements),
            "free_dofs": len(free_dofs),
            "constrained_dofs": len(constrained),
            "converged": True,
            "linear_static": True,
        }
        report = self._report(study, mesh, node_results, element_results, statistics, diagnostics)
        return {
            "result_type": "Static Structural Result",
            "scalars": {
                "max_displacement": statistics["max_displacement"],
                "max_von_mises_stress": statistics["max_von_mises_stress"],
                "min_safety_factor": statistics["min_safety_factor"],
                "max_principal_strain": statistics["max_principal_strain"],
            },
            "vectors": {
                "nodal_displacement": node_results["displacements"],
                "reaction_forces": node_results["reactions"],
                "load_vectors": self._load_vectors(force, nodes),
            },
            "statistics": statistics,
            "reports": [report],
            "history": [{
                "event": "linear_static_structural_solve",
                "timestamp": completed_at,
                "solver": self.solver_type,
            }],
            "visualization_metadata": {
                "contours": [
                    "Displacement",
                    "Von Mises Stress",
                    "Principal Stress",
                    "Principal Strain",
                    "Safety Factor",
                ],
                "vectors": ["Reaction", "Load"],
                "color_legends": {
                    "stress": {"min": statistics["min_von_mises_stress"], "max": statistics["max_von_mises_stress"]},
                    "displacement": {"min": 0.0, "max": statistics["max_displacement"]},
                    "safety_factor": {"min": statistics["min_safety_factor"], "max": statistics["max_safety_factor"]},
                },
            },
            "metadata": {
                "element_results": element_results,
                "node_results": node_results,
                "diagnostics": diagnostics,
            },
            "diagnostics": diagnostics,
            "report": report,
        }

    def validate(self, simulation_workspace, study):
        """Validate the structural study before execution."""

        errors = []
        warnings = []
        if study is None:
            return {"valid": False, "errors": ["Structural study was not found."], "warnings": []}
        if study.study_type != "Static Structural":
            errors.append("Structural solver requires a Static Structural study.")
        mesh = simulation_workspace.mesh_for(study.mesh_definition_id)
        if mesh is None:
            errors.append("Structural study requires a mesh definition.")
            return {"valid": False, "errors": errors, "warnings": warnings}
        nodes = self._nodes(mesh)
        elements = self._elements(mesh)
        if len(nodes) < 2:
            errors.append("Structural mesh requires at least two nodes.")
        if not elements:
            errors.append("Structural mesh requires at least one element.")
        material_ids = {item.material_id for item in simulation_workspace.structural_material_assignments if item.study_id == study.id}
        if not material_ids and study.material_references:
            material_ids = {item.get("material_id", "") for item in study.material_references}
        if not material_ids:
            errors.append("Structural study requires at least one material assignment.")
        if not study.boundary_condition_ids:
            errors.append("Structural study requires at least one boundary condition.")
        if not study.load_case_ids:
            errors.append("Structural study requires at least one load case.")
        node_ids = {node.get("id") for node in nodes}
        for element in elements:
            ids = list(element.get("node_ids", []))
            if len(ids) != 2 or ids[0] not in node_ids or ids[1] not in node_ids:
                errors.append("Structural element references invalid node IDs.")
            if float(element.get("area", 0.0)) <= 0.0:
                errors.append("Structural element area must be positive.")
        return {"valid": not errors, "errors": errors, "warnings": warnings}

    def _nodes(self, mesh):
        nodes = mesh.settings.get("nodes", mesh.metadata.get("nodes", []))
        return [self._node(item, index) for index, item in enumerate(nodes)]

    def _node(self, item, index):
        coordinates = item.get("coordinates", item)
        return {
            "id": item.get("id", f"node-{index + 1}"),
            "x": float(coordinates.get("x", 0.0)),
            "y": float(coordinates.get("y", 0.0)),
            "z": float(coordinates.get("z", 0.0)),
        }

    def _elements(self, mesh):
        return [dict(item) for item in mesh.settings.get("elements", mesh.metadata.get("elements", []))]

    def _materials(self, simulation_workspace, study):
        properties = {item.material_id: item for item in simulation_workspace.material_properties}
        assignments = [item for item in simulation_workspace.structural_material_assignments if item.study_id == study.id]
        fallback_material_id = ""
        if assignments:
            fallback_material_id = assignments[0].material_id
        elif study.material_references:
            fallback_material_id = study.material_references[0].get("material_id", "")
        if fallback_material_id and fallback_material_id not in properties:
            raise ValueError("Structural material assignment lacks engineering material properties.")
        return {
            "properties": properties,
            "assignments": assignments,
            "fallback_material_id": fallback_material_id,
        }

    def _element_stiffness(self, element, nodes, node_index, materials):
        start_id, end_id = element["node_ids"]
        start = nodes[node_index[start_id]]
        end = nodes[node_index[end_id]]
        dx = end["x"] - start["x"]
        dy = end["y"] - start["y"]
        dz = end["z"] - start["z"]
        length = sqrt(dx * dx + dy * dy + dz * dz)
        if length <= 0.0:
            raise ValueError("Structural element length must be positive.")
        direction = [dx / length, dy / length, dz / length]
        material_id = element.get("material_id") or materials["fallback_material_id"]
        material = materials["properties"].get(material_id)
        if material is None:
            raise ValueError("Structural element references missing engineering material properties.")
        area = float(element.get("area", 0.0))
        modulus = float(material.elastic_modulus)
        if modulus <= 0.0:
            raise ValueError("Structural material elastic modulus must be positive.")
        axial = modulus * area / length
        transform = direction + [-direction[0], -direction[1], -direction[2]]
        matrix = [[axial * transform[row] * transform[col] for col in range(6)] for row in range(6)]
        first = node_index[start_id] * 3
        second = node_index[end_id] * 3
        return {
            "id": element.get("id", str(uuid4())),
            "node_ids": [start_id, end_id],
            "dofs": [first, first + 1, first + 2, second, second + 1, second + 2],
            "matrix": matrix,
            "length": length,
            "direction": direction,
            "area": area,
            "material": material,
        }

    def _assemble(self, stiffness, dofs, matrix):
        for row, global_row in enumerate(dofs):
            for col, global_col in enumerate(dofs):
                stiffness[global_row][global_col] += matrix[row][col]

    def _apply_loads(self, force, simulation_workspace, study, nodes, node_index, elements, materials):
        for load_id in study.load_case_ids:
            load = next((item for item in simulation_workspace.load_cases if item.id == load_id and item.enabled), None)
            if load is None:
                continue
            if load.load_type in {"Point Force", "Distributed Force", "Pressure", "Remote Force", "Custom Load"}:
                self._apply_force_load(force, load, node_index)
            elif load.load_type == "Gravity":
                self._apply_gravity_load(force, load, nodes, node_index, elements, materials)
            elif load.load_type == "Moment":
                self._apply_force_load(force, load, node_index)

    def _apply_force_load(self, force, load, node_index):
        vector = self._vector(load.values)
        targets = load.target_references or [{"node_id": node_id} for node_id in node_index]
        factor = float(load.factors.get("scale", 1.0))
        for target in targets:
            node_id = target.get("node_id")
            if node_id not in node_index:
                continue
            base = node_index[node_id] * 3
            force[base] += vector[0] * factor
            force[base + 1] += vector[1] * factor
            force[base + 2] += vector[2] * factor

    def _apply_gravity_load(self, force, load, nodes, node_index, elements, materials):
        vector = self._vector(load.values, default={"z": -9.80665})
        node_by_id = {node["id"]: node for node in nodes}
        for element in elements:
            material_id = element.get("material_id") or materials["fallback_material_id"]
            material = materials["properties"].get(material_id)
            if material is None:
                continue
            start_id, end_id = element["node_ids"]
            if start_id not in node_index or end_id not in node_index:
                continue
            start = node_index[start_id]
            end = node_index[end_id]
            start_node = node_by_id[start_id]
            end_node = node_by_id[end_id]
            dx = end_node["x"] - start_node["x"]
            dy = end_node["y"] - start_node["y"]
            dz = end_node["z"] - start_node["z"]
            density = float(material.density)
            area = float(element.get("area", 0.0))
            length = float(element.get("length", 0.0)) or sqrt(dx * dx + dy * dy + dz * dz)
            mass = density * area * length
            for node in [start, end]:
                base = node * 3
                force[base] += 0.5 * mass * vector[0]
                force[base + 1] += 0.5 * mass * vector[1]
                force[base + 2] += 0.5 * mass * vector[2]

    def _constrained_dofs(self, simulation_workspace, study, node_index):
        constrained = set()
        for condition_id in study.boundary_condition_ids:
            condition = next((item for item in simulation_workspace.boundary_conditions if item.id == condition_id and item.enabled), None)
            if condition is None:
                continue
            targets = condition.target_references or []
            axes = condition.values.get("constrained_dofs")
            if axes is None:
                axes = ["x", "y", "z"] if condition.condition_type in {"Fixed", "Pinned", "Symmetry", "Remote Constraint"} else condition.values.get("axes", ["z"])
            axis_indices = {"x": 0, "y": 1, "z": 2}
            for target in targets:
                node_id = target.get("node_id")
                if node_id not in node_index:
                    continue
                base = node_index[node_id] * 3
                for axis in axes:
                    if axis in axis_indices:
                        constrained.add(base + axis_indices[axis])
        return constrained

    def _element_results(self, element_data, displacement):
        results = []
        for data in element_data:
            dofs = data["dofs"]
            local = [displacement[index] for index in dofs]
            direction = data["direction"]
            axial_displacement = (
                (local[3] - local[0]) * direction[0]
                + (local[4] - local[1]) * direction[1]
                + (local[5] - local[2]) * direction[2]
            )
            strain = axial_displacement / data["length"]
            stress = data["material"].elastic_modulus * strain
            von_mises = abs(stress)
            yield_strength = float(data["material"].yield_strength or 0.0)
            safety_factor = yield_strength / von_mises if von_mises > 0.0 and yield_strength > 0.0 else float("inf")
            results.append({
                "element_id": data["id"],
                "node_ids": list(data["node_ids"]),
                "strain": strain,
                "principal_strain": strain,
                "normal_stress": stress,
                "principal_stress": stress,
                "von_mises_stress": von_mises,
                "shear_stress": 0.0,
                "axial_force": stress * data["area"],
                "safety_factor": safety_factor,
            })
        return results

    def _node_results(self, nodes, displacement, reactions):
        displacements = {}
        reaction_forces = {}
        for index, node in enumerate(nodes):
            base = index * 3
            vector = {
                "x": displacement[base],
                "y": displacement[base + 1],
                "z": displacement[base + 2],
            }
            vector["magnitude"] = sqrt(vector["x"] ** 2 + vector["y"] ** 2 + vector["z"] ** 2)
            reaction = {
                "x": reactions[base],
                "y": reactions[base + 1],
                "z": reactions[base + 2],
            }
            reaction["magnitude"] = sqrt(reaction["x"] ** 2 + reaction["y"] ** 2 + reaction["z"] ** 2)
            displacements[node["id"]] = vector
            reaction_forces[node["id"]] = reaction
        return {"displacements": displacements, "reactions": reaction_forces}

    def _statistics(self, node_results, element_results):
        displacements = [item["magnitude"] for item in node_results["displacements"].values()]
        stresses = [item["von_mises_stress"] for item in element_results]
        strains = [abs(item["principal_strain"]) for item in element_results]
        safety = [item["safety_factor"] for item in element_results if isfinite(item["safety_factor"])]
        return {
            "max_displacement": max(displacements or [0.0]),
            "min_displacement": min(displacements or [0.0]),
            "max_von_mises_stress": max(stresses or [0.0]),
            "min_von_mises_stress": min(stresses or [0.0]),
            "max_principal_stress": max([item["principal_stress"] for item in element_results] or [0.0]),
            "min_principal_stress": min([item["principal_stress"] for item in element_results] or [0.0]),
            "max_principal_strain": max(strains or [0.0]),
            "min_principal_strain": min(strains or [0.0]),
            "min_safety_factor": min(safety or [float("inf")]),
            "max_safety_factor": max(safety or [float("inf")]),
            "element_count": len(element_results),
            "node_count": len(node_results["displacements"]),
        }

    def _report(self, study, mesh, node_results, element_results, statistics, diagnostics):
        return {
            "id": str(uuid4()),
            "title": f"{study.name} Structural Analysis Report",
            "study_id": study.id,
            "generated_at": diagnostics["completed_at"],
            "study_summary": {
                "name": study.name,
                "type": study.study_type,
                "status": "Solved",
            },
            "material_summary": list(study.material_references),
            "load_summary": list(study.load_case_ids),
            "constraint_summary": list(study.boundary_condition_ids),
            "mesh_summary": {
                "mesh_id": mesh.id,
                "element_type": mesh.element_type,
                "element_size": mesh.element_size,
                "quality": dict(mesh.quality),
            },
            "solver_statistics": diagnostics,
            "maximum_displacement": statistics["max_displacement"],
            "maximum_stress": statistics["max_von_mises_stress"],
            "safety_factor": statistics["min_safety_factor"],
            "warnings": [],
            "errors": [],
            "recommendations": self._recommendations(statistics),
        }

    def _recommendations(self, statistics):
        recommendations = []
        if statistics["min_safety_factor"] < 1.0:
            recommendations.append("Increase section area, improve material strength, or reduce applied load.")
        if statistics["max_displacement"] <= 0.0:
            recommendations.append("Review load and constraint setup if zero displacement is unexpected.")
        return recommendations

    def _load_vectors(self, force, nodes):
        vectors = {}
        for index, node in enumerate(nodes):
            base = index * 3
            vectors[node["id"]] = {"x": force[base], "y": force[base + 1], "z": force[base + 2]}
        return vectors

    def _solve_linear_system(self, matrix, vector):
        size = len(vector)
        augmented = [list(matrix[row]) + [vector[row]] for row in range(size)]
        for pivot in range(size):
            best = max(range(pivot, size), key=lambda row: abs(augmented[row][pivot]))
            if abs(augmented[best][pivot]) <= 1e-12:
                raise ValueError("Structural stiffness matrix is singular; check constraints and connectivity.")
            if best != pivot:
                augmented[pivot], augmented[best] = augmented[best], augmented[pivot]
            pivot_value = augmented[pivot][pivot]
            for col in range(pivot, size + 1):
                augmented[pivot][col] /= pivot_value
            for row in range(size):
                if row == pivot:
                    continue
                factor = augmented[row][pivot]
                if factor == 0.0:
                    continue
                for col in range(pivot, size + 1):
                    augmented[row][col] -= factor * augmented[pivot][col]
        return [augmented[row][size] for row in range(size)]

    def _multiply(self, matrix, vector):
        return [sum(value * vector[col] for col, value in enumerate(row)) for row in matrix]

    def _subtract(self, left, right):
        return [left[index] - right[index] for index in range(len(left))]

    def _vector(self, values, default=None):
        source = dict(default or {})
        source.update(values or {})
        if "vector" in source:
            vector = source["vector"]
            if isinstance(vector, dict):
                return [float(vector.get("x", 0.0)), float(vector.get("y", 0.0)), float(vector.get("z", 0.0))]
            return [float(vector[0]), float(vector[1]), float(vector[2])]
        magnitude = float(source.get("magnitude", 1.0))
        direction = source.get("direction", source)
        vector = [float(direction.get("x", 0.0)), float(direction.get("y", 0.0)), float(direction.get("z", 0.0))]
        length = sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)
        if length == 0.0:
            return [0.0, 0.0, 0.0]
        return [magnitude * item / length for item in vector]

    def _timestamp(self):
        return datetime.now(timezone.utc).isoformat()

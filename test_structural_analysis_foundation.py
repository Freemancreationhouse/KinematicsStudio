from pathlib import Path
from tempfile import TemporaryDirectory

from engine.commands.structural_simulation_command import RunStructuralStudyCommand
from engine.product import EngineeringMaterial
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_structural_analysis_foundation_linear_static_solver_command_and_persistence():
    workspace = Workspace("Structural Analysis Project")
    simulation = workspace.simulation_workspace.initialize()

    material = workspace.product_manager.engineering_material_manager.add_item(
        EngineeringMaterial("Structural Steel", density=7850.0)
    )
    properties = simulation.register_material_properties(
        material,
        density=7850.0,
        elastic_modulus=200_000_000_000.0,
        poisson_ratio=0.30,
        yield_strength=250_000_000.0,
        ultimate_strength=400_000_000.0,
    )
    project = simulation.create_project("Structural Project", "Release 1.8 Batch B")
    study = simulation.create_structural_study(
        project,
        "Axial Member Study",
        target_geometry=[{"body_id": "member-body"}],
        solver_settings={"analysis_type": "Linear Static"},
        visualization_settings={"stress_contour": True},
    )
    assignment = simulation.assign_structural_material(
        study,
        material,
        "Body",
        [{"body_id": "member-body"}],
        properties,
    )
    fixed = simulation.create_boundary_condition(
        "Fixed Left Node",
        "Fixed",
        target_references=[{"node_id": "n1"}],
    )
    roller = simulation.create_boundary_condition(
        "Lateral Right Constraint",
        "Roller",
        target_references=[{"node_id": "n2"}],
        values={"axes": ["y", "z"]},
    )
    load = simulation.create_load_case(
        "Axial Tension",
        "Point Force",
        target_references=[{"node_id": "n2"}],
        values={"vector": {"x": 1000.0, "y": 0.0, "z": 0.0}},
    )
    study.boundary_condition_ids.extend([fixed.id, roller.id])
    study.load_case_ids.append(load.id)
    simulation.create_load_combination("Service", {load.id: 1.0})
    mesh = simulation.generate_structural_mesh(
        study,
        nodes=[
            {"id": "n1", "x": 0.0, "y": 0.0, "z": 0.0},
            {"id": "n2", "x": 2.0, "y": 0.0, "z": 0.0},
        ],
        elements=[
            {"id": "e1", "node_ids": ["n1", "n2"], "area": 0.01, "material_id": material.id},
        ],
        element_size=2.0,
        element_type="Structural Line",
    )

    assert assignment.properties_id == properties.id
    assert mesh.quality["quality_evaluated"] is True

    command = RunStructuralStudyCommand(workspace, study)
    workspace.command_manager.execute(command)

    result = simulation.results[-1]
    report = result.reports[0]
    assert study.status == "Solved"
    assert abs(result.scalars["max_displacement"] - 0.000001) < 1e-12
    assert abs(result.scalars["max_von_mises_stress"] - 100000.0) < 1e-6
    assert abs(result.vectors["reaction_forces"]["n1"]["x"] + 1000.0) < 1e-6
    assert abs(result.scalars["min_safety_factor"] - 2500.0) < 1e-6
    assert report["maximum_displacement"] == result.scalars["max_displacement"]
    assert simulation.visualizations[-1].result_id == result.id
    assert simulation.structural_execution_history[-1].status == "Completed"
    assert workspace.command_manager.undo_count == 1

    workspace.command_manager.undo()
    assert workspace.simulation_workspace.results == []
    assert workspace.command_manager.redo_count == 1

    workspace.command_manager.redo()
    assert len(workspace.simulation_workspace.results) == 1
    assert workspace.simulation_workspace.studies[0].status == "Solved"

    with TemporaryDirectory() as directory:
        path = Path(directory) / "structural_analysis.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.simulation_workspace.load_from_settings()
    restored_simulation = restored.simulation_workspace
    assert len(restored_simulation.structural_material_assignments) == 1
    assert len(restored_simulation.structural_execution_history) == 1
    assert len(restored_simulation.results) == 1
    assert len(restored_simulation.visualizations) == 1
    assert restored_simulation.results[0].scalars["max_von_mises_stress"] == 100000.0
    assert restored_simulation.diagnostics().to_dict()["statistics"]["structural_solved_studies"] == 1

    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []


if __name__ == "__main__":
    test_structural_analysis_foundation_linear_static_solver_command_and_persistence()
    print("structural-analysis-foundation-ok")

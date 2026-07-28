from pathlib import Path
from tempfile import TemporaryDirectory

from engine.product import EngineeringMaterial
from engine.simulation import (
    EngineeringSimulationManager,
    SimulationMeshDefinition,
    SimulationResult,
    SimulationSolverDefinition,
    SimulationVisualization,
)
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_engineering_simulation_foundation_metadata_persistence_and_validation():
    workspace = Workspace("Engineering Simulation Project")
    simulation = workspace.simulation_workspace.initialize()

    material = workspace.product_manager.engineering_material_manager.add_item(
        EngineeringMaterial("Simulation Aluminum", density=2700.0)
    )
    project = simulation.create_project("Building and Product Simulation", "Release 1.8 foundation")
    material_properties = simulation.register_material_properties(
        material,
        density=2700.0,
        elastic_modulus=69_000_000_000.0,
        poisson_ratio=0.33,
        yield_strength=275_000_000.0,
        ultimate_strength=310_000_000.0,
        thermal_conductivity=205.0,
        specific_heat=900.0,
        thermal_expansion=0.000023,
        solar_absorptance=0.35,
        reflectance=0.55,
        transmittance=0.0,
        emissivity=0.1,
        air_permeability={"classification": "sealed"},
        mechanical={"source": "engineering material library"},
        environmental={"recyclable": True},
    )
    boundary = simulation.create_boundary_condition(
        "Fixed Base",
        "Fixed",
        target_references=[{"body_id": "body-reference", "face_id": "bottom"}],
    )
    load = simulation.create_load_case(
        "Service Wind",
        "Wind Load",
        target_references=[{"body_id": "body-reference", "face_id": "windward"}],
        values={"pressure": 1.2},
    )
    combination = simulation.create_load_combination("ULS", {load.id: 1.5})
    study = simulation.create_study(
        project,
        "Static Building Frame",
        "Static Structural",
        target_geometry=[{"body_id": "body-reference"}],
        material_references=[{"material_id": material.id, "properties_id": material_properties.id}],
        solver_settings={"tolerance": 0.001},
        visualization_settings={"color_map": "Stress"},
    )
    study.boundary_condition_ids.append(boundary.id)
    study.load_case_ids.append(load.id)
    mesh = simulation.create_mesh_definition(
        study,
        element_size=25.0,
        element_type="Tetrahedral",
        quality={"skewness": "tracked"},
        adaptive_refinement={"enabled": True, "metric": "gradient"},
    )
    solver = simulation.register_solver(
        "Structural Solver Interface",
        "Structural",
        ["Static Structural"],
        version="1.8-interface",
        diagnostics={"numerical_solver": False},
    )
    simulation.select_solver(study, solver)
    schedule = simulation.manager.schedule_execution(study)
    result = simulation.create_result(
        study,
        "Static Structural Metadata Result",
        scalars={"max_displacement": None},
        vectors={"reaction_forces": []},
        statistics={"samples": 0},
        reports=[{"title": "Foundation report"}],
        history=[{"event": "result metadata created"}],
        visualization_metadata={"color_maps": ["Stress", "Displacement"]},
    )
    visualization = simulation.create_visualization(
        study,
        result,
        color_legend={"name": "Stress Legend"},
        result_overlays=[{"type": "scalar"}],
        vector_overlays=[{"type": "force"}],
        section_views=[{"name": "Midspan Section"}],
        animation={"enabled": False},
        probes=[{"name": "Probe A"}],
        measurements=[{"name": "Deflection"}],
        display_settings={"visible": True},
    )

    assert isinstance(simulation.manager, EngineeringSimulationManager)
    assert isinstance(mesh, SimulationMeshDefinition)
    assert isinstance(solver, SimulationSolverDefinition)
    assert isinstance(result, SimulationResult)
    assert isinstance(visualization, SimulationVisualization)
    assert schedule["numerical_solver_executed"] is False
    assert study.status == "Scheduled"
    assert combination.load_case_factors[load.id] == 1.5

    validation = simulation.validate()
    diagnostics = simulation.diagnostics().to_dict()
    assert validation["valid"] is True
    assert diagnostics["projects"] == 1
    assert diagnostics["studies"] == 1
    assert diagnostics["material_properties"] == 1
    assert diagnostics["boundary_conditions"] == 1
    assert diagnostics["load_cases"] == 1
    assert diagnostics["meshes"] == 1
    assert diagnostics["solvers"] == 1
    assert diagnostics["results"] == 1
    assert diagnostics["visualizations"] == 1
    assert diagnostics["statistics"]["numerical_solvers_executed"] == 0

    assert list(workspace.scene3d.entities()) == []
    assert getattr(workspace.product_manager, "bodies", []) == []
    assert getattr(workspace.product_manager, "features", []) == []
    assert workspace.command_manager.undo_stack == []
    assert workspace.command_manager.redo_stack == []

    with TemporaryDirectory() as directory:
        path = Path(directory) / "engineering_simulation.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.simulation_workspace.load_from_settings()
    restored_simulation = restored.simulation_workspace

    assert restored_simulation.state.initialized is True
    assert len(restored_simulation.projects) == 1
    assert len(restored_simulation.studies) == 1
    assert len(restored_simulation.material_properties) == 1
    assert len(restored_simulation.boundary_conditions) == 1
    assert len(restored_simulation.load_cases) == 1
    assert len(restored_simulation.load_combinations) == 1
    assert len(restored_simulation.mesh_definitions) == 1
    assert len(restored_simulation.solvers) == 1
    assert len(restored_simulation.results) == 1
    assert len(restored_simulation.visualizations) == 1
    assert restored_simulation.validate()["valid"] is True
    assert restored_simulation.studies[0].status == "Scheduled"
    assert restored_simulation.studies[0].solver_id == restored_simulation.solvers[0].id
    assert restored_simulation.studies[0].mesh_definition_id == restored_simulation.mesh_definitions[0].id

    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []
    assert restored.command_manager.undo_stack == []
    assert restored.command_manager.redo_stack == []


if __name__ == "__main__":
    test_engineering_simulation_foundation_metadata_persistence_and_validation()
    print("engineering-simulation-foundation-ok")

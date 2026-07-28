from pathlib import Path
from tempfile import TemporaryDirectory

from engine.commands.structural_simulation_command import RunThermalStudyCommand
from engine.product import EngineeringMaterial
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_thermal_simulation_foundation_solver_reports_visualization_and_persistence():
    workspace = Workspace("Thermal Simulation Project")
    simulation = workspace.simulation_workspace.initialize()

    insulation = workspace.product_manager.engineering_material_manager.add_item(
        EngineeringMaterial("Thermal Panel", density=1000.0)
    )
    thermal_properties = simulation.register_thermal_material_properties(
        insulation,
        thermal_conductivity=10.0,
        specific_heat=900.0,
        density=1000.0,
        thermal_expansion=0.00001,
        thermal_diffusivity=0.000011,
        heat_capacity=900000.0,
        solar_absorptance=0.4,
        solar_reflectance=0.5,
        emissivity=0.85,
        surface_roughness={"class": "smooth"},
        thermal_resistance=0.1,
        u_value=10.0,
        environmental={"assembly": "test wall"},
    )
    project = simulation.create_project("Thermal Project", "Release 1.8 Batch D")
    study = simulation.create_thermal_study(
        project,
        "Wall Heat Transfer",
        "Building Thermal",
        target_geometry=[{"assembly_id": "wall-assembly"}],
        solver_settings={"analysis_type": "Steady-State Heat Transfer"},
        visualization_settings={"temperature_contours": True},
    )
    assignment = simulation.assign_thermal_material(
        study,
        insulation,
        [{"assembly_id": "wall-assembly"}],
        thermal_properties,
    )
    fixed = simulation.create_boundary_condition(
        "Interior Temperature",
        "Fixed Temperature",
        [{"node_id": "inside"}],
        {"temperature": 100.0},
    )
    convection = simulation.create_boundary_condition(
        "Exterior Convection",
        "Convection",
        [{"node_id": "outside"}],
        {"coefficient": 10.0, "area": 1.0, "ambient_temperature": 0.0},
    )
    radiation = simulation.create_boundary_condition(
        "Exterior Radiation Metadata",
        "Radiation",
        [{"node_id": "outside"}],
        {"linearized_coefficient": 0.0, "ambient_temperature": 0.0},
    )
    study.boundary_condition_ids.extend([fixed.id, convection.id, radiation.id])
    source = simulation.create_heat_source(
        study,
        "Equipment Heat",
        "Equipment Heat Source",
        [{"node_id": "outside"}],
        {"heat": 100.0},
    )
    assembly = simulation.create_thermal_assembly(
        study,
        "Exterior Wall",
        "Wall Assembly",
        [{"material_id": insulation.id, "thickness": 0.2}],
        [{"node_id": "inside"}, {"node_id": "outside"}],
        {"linear_bridge_count": 1},
        {"room": "Lab"},
    )
    mesh = simulation.generate_thermal_mesh(
        study,
        nodes=[
            {"id": "inside", "x": 0.0, "y": 0.0, "z": 0.0},
            {"id": "outside", "x": 1.0, "y": 0.0, "z": 0.0},
        ],
        elements=[
            {"id": "wall-e1", "node_ids": ["inside", "outside"], "area": 1.0, "material_id": insulation.id, "region": "wall"},
        ],
        element_size=1.0,
        element_type="Thermal Line",
        adaptive_refinement={"boundary_refinement": True},
        metadata={"thermal_region": "wall"},
    )

    assert assignment["thermal_properties_id"] == thermal_properties.id
    assert source.id in study.metadata["heat_source_ids"]
    assert assembly.assembly_type == "Wall Assembly"
    assert mesh.quality["quality_evaluated"] is True

    command = RunThermalStudyCommand(workspace, study)
    workspace.command_manager.execute(command)

    result = simulation.results[-1]
    report = result.reports[0]
    building_report = result.reports[-1]
    assert study.status == "Solved"
    assert abs(result.vectors["temperature_distribution"]["outside"]["temperature"] - 55.0) < 1e-9
    assert result.scalars["maximum_temperature"] == 100.0
    assert abs(result.statistics["maximum_heat_flux"] - 450.0) < 1e-9
    assert result.statistics["thermal_assembly_count"] == 1
    assert building_report["u_value_summary"]["Exterior Wall"] == 50.0
    assert report["temperature_summary"]["maximum"] == 100.0
    assert simulation.visualizations[-1].display_settings["temperature_contours"] is True
    assert simulation.thermal_execution_history[-1].status == "Completed"

    workspace.command_manager.undo()
    assert workspace.simulation_workspace.results == []
    workspace.command_manager.redo()
    assert len(workspace.simulation_workspace.results) == 1

    with TemporaryDirectory() as directory:
        path = Path(directory) / "thermal_simulation.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.simulation_workspace.load_from_settings()
    restored_simulation = restored.simulation_workspace
    assert len(restored_simulation.thermal_material_properties) == 1
    assert len(restored_simulation.heat_sources) == 1
    assert len(restored_simulation.thermal_assemblies) == 1
    assert len(restored_simulation.thermal_execution_history) == 1
    assert len(restored_simulation.results) == 1
    assert restored_simulation.diagnostics().to_dict()["statistics"]["thermal_solved_studies"] == 1

    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []


if __name__ == "__main__":
    test_thermal_simulation_foundation_solver_reports_visualization_and_persistence()
    print("thermal-simulation-foundation-ok")

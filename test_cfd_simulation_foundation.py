from pathlib import Path
from tempfile import TemporaryDirectory

from engine.commands.structural_simulation_command import RunCFDStudyCommand
from engine.product import EngineeringMaterial
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_cfd_simulation_foundation_solver_reports_visualization_and_persistence():
    workspace = Workspace("CFD Simulation Project")
    simulation = workspace.simulation_workspace.initialize()

    air = workspace.product_manager.engineering_material_manager.add_item(
        EngineeringMaterial("CFD Air", density=1.204)
    )
    simulation.register_material_properties(
        air,
        density=1.204,
        thermal_conductivity=0.026,
        specific_heat=1005.0,
        environmental={"fluid": "air"},
    )

    project = simulation.create_project("CFD Project", "Release 1.8 Batch G")
    thermal_study = simulation.create_thermal_study(project, "Thermal Reuse", "Building Thermal")
    simulation.create_heat_source(
        thermal_study,
        "Occupant Heat",
        "Occupancy Heat Source",
        target_references=[{"zone_id": "office-zone"}],
        values={"heat": 800.0},
    )
    daylight_study = simulation.create_daylight_study(project, "Daylight Reuse", "Building Daylight")
    daylight_zone = simulation.create_daylight_zone(daylight_study, "Daylight Office", "Room", area=80.0)
    simulation.create_daylight_opening(
        daylight_study,
        "Operable Window",
        "Window",
        target_references=[{"face_id": "window-west"}],
        area=4.0,
        transmittance=0.6,
        room_id=daylight_zone.id,
    )
    energy_study = simulation.create_energy_study(project, "Energy Reuse", "Building Energy Study")
    simulation.create_energy_schedule(
        energy_study,
        "Ventilation Schedule",
        "Ventilation",
        values=[1.0] * 12,
        gains={"air_change_watts_per_k": 12.0},
    )

    study = simulation.create_cfd_study(
        project,
        "Office Airflow Study",
        "Indoor Airflow Study",
        target_geometry=[{"room_id": "office-zone"}],
        solver_settings={
            "residual_tolerance": 0.75,
            "target_air_change_rate": 3.0,
            "comfort_velocity_limit": 2.0,
        },
        visualization_settings={"velocity_field": True, "pressure_field": True},
    )
    domain = simulation.create_cfd_domain(
        study,
        "Office Air Domain",
        "Indoor Domain",
        extents={"length": 10.0, "width": 8.0, "height": 3.0, "volume": 240.0, "hydraulic_diameter": 3.2},
        reference_elevation=0.0,
        reference_pressure=101325.0,
        gravity_metadata={"enabled": True, "z": -9.81},
        fluid_properties={"density": 1.204, "dynamic_viscosity": 1.825e-5},
        compressibility_metadata={"incompressible": True},
        turbulence_metadata={"model": "metadata-k-epsilon", "intensity": 0.05},
        region_metadata={"thermal_zone": "office-zone"},
    )
    inlet = simulation.create_cfd_boundary_condition(
        study,
        "Supply Diffuser",
        "HVAC Diffuser",
        target_references=[{"face_id": "ceiling-diffuser"}],
        values={"area": 0.25, "speed": 3.0, "direction": {"x": 1.0, "y": 0.0, "z": -0.15}},
    )
    outlet = simulation.create_cfd_boundary_condition(
        study,
        "Return Grille",
        "Pressure Outlet",
        target_references=[{"face_id": "return-grille"}],
        values={"area": 0.3, "estimated_speed": 2.5, "pressure": 101300.0},
    )
    window = simulation.create_cfd_boundary_condition(
        study,
        "Operable Window Opening",
        "Window Opening",
        target_references=[{"face_id": "window-west"}],
        values={"area": 1.0, "speed": 0.6, "direction": {"x": 1.0, "y": 0.2, "z": 0.0}},
    )
    simulation.create_cfd_flow_source(
        study,
        "Supply Air Source",
        "Supply Air",
        target_references=[{"face_id": "ceiling-diffuser"}],
        values={"flow_rate": 0.42, "speed": 1.5, "direction": {"x": 1.0, "y": 0.0, "z": -0.2}},
    )
    simulation.create_cfd_flow_source(
        study,
        "Cross Ventilation",
        "Natural Ventilation",
        target_references=[{"face_id": "window-west"}],
        values={"flow_rate": 0.15, "speed": 0.7, "direction": {"x": 1.0, "y": 0.2, "z": 0.0}},
    )
    simulation.create_cfd_flow_source(
        study,
        "Urban Wind",
        "Wind Profile",
        target_references=[{"site_id": "site"}],
        values={"speed": 2.0, "direction": {"x": 1.0, "y": 0.0, "z": 0.0}},
    )
    mesh = simulation.generate_cfd_mesh(
        study,
        nodes=[
            {"id": "n1", "x": 0.0, "y": 0.0, "z": 1.2},
            {"id": "n2", "x": 4.0, "y": 2.0, "z": 1.2},
            {"id": "n3", "x": 8.0, "y": 4.0, "z": 1.2},
            {"id": "n4", "x": 10.0, "y": 8.0, "z": 2.4},
        ],
        cells=[{"id": "cell-1", "node_ids": ["n1", "n2", "n3", "n4"], "region": "office-zone"}],
        boundary_layer_metadata={"first_layer_height": 0.02, "growth": 1.2},
        near_wall_refinement={"enabled": True, "target_size": 0.15},
        region_refinement={"office-zone": 0.25},
    )

    assert domain.domain_type == "Indoor Domain"
    assert inlet.boundary_type == "HVAC Diffuser"
    assert outlet.boundary_type == "Pressure Outlet"
    assert window.boundary_type == "Window Opening"
    assert mesh.quality["quality_evaluated"] is True

    command = RunCFDStudyCommand(workspace, study)
    workspace.command_manager.execute(command)

    result = simulation.results[-1]
    report = result.reports[0]
    assert study.status == "Solved"
    assert result.result_type == "CFD Airflow Result"
    assert result.scalars["maximum_velocity"] > 0.0
    assert result.scalars["average_velocity"] > 0.0
    assert result.scalars["air_change_rate"] > 0.0
    assert "velocity_vectors" in result.vectors
    assert "pressure_contours" in result.vectors
    assert "streamlines_metadata" in result.vectors
    assert result.statistics["ventilation_summary"]["cross_ventilation"] is True
    assert result.statistics["building_cfd"]["room_airflow"] is True
    assert result.metadata["thermal_reuse"] is True
    assert result.metadata["daylight_reuse"] is True
    assert result.metadata["energy_reuse"] is True
    assert report["fluid_domain"]["name"] == "Office Air Domain"
    assert simulation.visualizations[-1].display_settings["velocity_field"] is True
    assert simulation.cfd_execution_history[-1].status == "Completed"

    workspace.command_manager.undo()
    assert workspace.simulation_workspace.results == []
    workspace.command_manager.redo()
    assert len(workspace.simulation_workspace.results) == 1

    with TemporaryDirectory() as directory:
        path = Path(directory) / "cfd_simulation.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.simulation_workspace.load_from_settings()
    restored_simulation = restored.simulation_workspace
    assert len(restored_simulation.cfd_domains) == 1
    assert len(restored_simulation.cfd_boundary_conditions) == 3
    assert len(restored_simulation.cfd_flow_sources) == 3
    assert len(restored_simulation.cfd_execution_history) == 1
    assert len(restored_simulation.results) == 1
    assert restored_simulation.diagnostics().to_dict()["statistics"]["cfd_solved_studies"] == 1

    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []


if __name__ == "__main__":
    test_cfd_simulation_foundation_solver_reports_visualization_and_persistence()
    print("cfd-simulation-foundation-ok")

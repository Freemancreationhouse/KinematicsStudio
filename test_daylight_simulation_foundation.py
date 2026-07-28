from pathlib import Path
from tempfile import TemporaryDirectory

from engine.commands.structural_simulation_command import RunDaylightStudyCommand
from engine.product import EngineeringMaterial
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_daylight_simulation_foundation_solver_reports_visualization_and_persistence():
    workspace = Workspace("Daylight Simulation Project")
    simulation = workspace.simulation_workspace.initialize()

    glazing = workspace.product_manager.engineering_material_manager.add_item(
        EngineeringMaterial("Daylight Glazing", density=2500.0)
    )
    material_properties = simulation.register_material_properties(
        glazing,
        density=2500.0,
        solar_absorptance=0.2,
        reflectance=0.1,
        transmittance=0.7,
        emissivity=0.84,
        environmental={"daylight_material": True},
    )
    project = simulation.create_project("Daylight Project", "Release 1.8 Batch E")
    study = simulation.create_daylight_study(
        project,
        "Studio Daylight Study",
        "Building Daylight",
        target_geometry=[{"room_id": "studio"}],
        solver_settings={"analysis_type": "Static Daylight"},
        visualization_settings={"lux_heat_map": True},
    )
    study.material_references.append({"material_id": glazing.id, "properties_id": material_properties.id})
    location = simulation.set_daylight_location(
        study,
        latitude=12.9716,
        longitude=77.5946,
        elevation=920.0,
        time_zone=5.5,
        north_orientation=0.0,
        site_metadata={"city": "Bengaluru"},
        weather_metadata={"source": "design-day"},
        sky_condition_metadata={"condition": "clear"},
        season_metadata={"season": "summer"},
        date="2026-03-21",
        time="12:00",
    )
    sky = simulation.create_sky_model(
        study,
        "Clear Design Sky",
        "Clear Sky",
        luminance=12000.0,
        diffuse_illuminance=10000.0,
        direct_normal_illuminance=60000.0,
        metadata={"cie": "clear"},
    )
    room = simulation.create_daylight_zone(
        study,
        "Studio Room",
        "Room",
        area=25.0,
        target_references=[{"room_id": "studio"}],
    )
    facade = simulation.create_daylight_zone(
        study,
        "South Facade",
        "Facade",
        area=12.0,
        target_references=[{"facade_id": "south"}],
    )
    window = simulation.create_daylight_opening(
        study,
        "South Window",
        "Window",
        target_references=[{"opening_id": "window-south"}],
        area=4.0,
        transmittance=0.7,
        orientation={"azimuth": 180.0, "tilt": 90.0},
        room_id=room.id,
        facade_id=facade.id,
    )
    room.opening_ids.append(window.id)
    facade.opening_ids.append(window.id)
    mesh = simulation.generate_daylight_mesh(
        study,
        points=[
            {"id": "p1", "x": 1.0, "y": 1.0, "z": 0.8, "zone_id": room.id},
            {"id": "p2", "x": 3.0, "y": 2.0, "z": 0.8, "zone_id": room.id},
        ],
        element_size=1.0,
        metadata={"sensor_grid": "workplane"},
    )

    assert location.site_metadata["city"] == "Bengaluru"
    assert sky.model_type == "Clear Sky"
    assert mesh.quality["quality_evaluated"] is True

    command = RunDaylightStudyCommand(workspace, study)
    workspace.command_manager.execute(command)

    result = simulation.results[-1]
    report = result.reports[0]
    assert study.status == "Solved"
    assert result.scalars["average_lux"] > 0.0
    assert result.scalars["maximum_lux"] >= result.scalars["minimum_lux"]
    assert result.scalars["daylight_factor"] > 0.0
    assert "solar_vectors" in result.vectors
    assert "sda_metadata" in result.statistics
    assert report["location_summary"]["site_metadata"]["city"] == "Bengaluru"
    assert report["window_summary"][0]["name"] == "South Window"
    assert simulation.visualizations[-1].display_settings["lux_heat_map"] is True
    assert simulation.daylight_execution_history[-1].status == "Completed"

    workspace.command_manager.undo()
    assert workspace.simulation_workspace.results == []
    workspace.command_manager.redo()
    assert len(workspace.simulation_workspace.results) == 1

    with TemporaryDirectory() as directory:
        path = Path(directory) / "daylight_simulation.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.simulation_workspace.load_from_settings()
    restored_simulation = restored.simulation_workspace
    assert len(restored_simulation.daylight_locations) == 1
    assert len(restored_simulation.sky_models) == 1
    assert len(restored_simulation.daylight_openings) == 1
    assert len(restored_simulation.daylight_zones) == 2
    assert len(restored_simulation.daylight_execution_history) == 1
    assert len(restored_simulation.results) == 1
    assert restored_simulation.diagnostics().to_dict()["statistics"]["daylight_solved_studies"] == 1

    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []


if __name__ == "__main__":
    test_daylight_simulation_foundation_solver_reports_visualization_and_persistence()
    print("daylight-simulation-foundation-ok")

from pathlib import Path
from tempfile import TemporaryDirectory

from engine.commands.structural_simulation_command import RunEnergyStudyCommand
from engine.product import EngineeringMaterial
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_energy_analysis_foundation_solver_reports_visualization_and_persistence():
    workspace = Workspace("Energy Analysis Project")
    simulation = workspace.simulation_workspace.initialize()

    wall_material = workspace.product_manager.engineering_material_manager.add_item(
        EngineeringMaterial("Energy Wall Assembly", density=1850.0)
    )
    glazing = workspace.product_manager.engineering_material_manager.add_item(
        EngineeringMaterial("Energy Glazing", density=2500.0)
    )
    wall_thermal = simulation.register_thermal_material_properties(
        wall_material,
        thermal_conductivity=0.35,
        specific_heat=900.0,
        density=1850.0,
        thermal_resistance=2.5,
        u_value=0.4,
        solar_absorptance=0.55,
        emissivity=0.88,
        environmental={"energy_reuse": True},
    )
    glazing_thermal = simulation.register_thermal_material_properties(
        glazing,
        thermal_conductivity=1.0,
        specific_heat=750.0,
        density=2500.0,
        thermal_resistance=0.5,
        u_value=2.0,
        solar_absorptance=0.25,
        solar_reflectance=0.15,
        emissivity=0.84,
        environmental={"visible_transmittance": 0.68},
    )

    project = simulation.create_project("Energy Project", "Release 1.8 Batch F")
    daylight_study = simulation.create_daylight_study(project, "Reference Daylight", "Building Daylight")
    daylight_zone = simulation.create_daylight_zone(daylight_study, "Office Daylight Zone", "Room", area=90.0)
    simulation.create_daylight_opening(
        daylight_study,
        "South Glazing Reference",
        "Window",
        target_references=[{"face_id": "south-window"}],
        area=18.0,
        transmittance=0.68,
        orientation={"azimuth": 180.0, "tilt": 90.0},
        room_id=daylight_zone.id,
    )

    study = simulation.create_energy_study(
        project,
        "Office Energy Study",
        "Annual Energy Study",
        target_geometry=[{"building_id": "office-block"}],
        solver_settings={
            "floor_area": 120.0,
            "heating_setpoint": 20.0,
            "cooling_setpoint": 24.0,
            "infiltration_watts_per_k": 8.0,
            "carbon_factor_kg_per_kwh": 0.42,
            "energy_rate_per_kwh": 0.12,
            "renewable_contribution_kwh": 1800.0,
            "target_eui": 100.0,
        },
        visualization_settings={"energy_dashboard": True, "monthly_charts": True},
    )
    climate = simulation.set_energy_climate(
        study,
        weather_metadata={"source": "design-weather", "city": "Bengaluru"},
        temperature_profile=[21.0, 23.0, 26.0, 28.0, 29.0, 27.0, 25.0, 25.0, 24.0, 23.0, 21.0, 20.0],
        humidity_metadata={"average_relative_humidity": 0.62},
        wind_metadata={"average_speed_m_per_s": 2.3},
        solar_radiation_metadata={"monthly_kwh_per_m2": [130.0, 140.0, 160.0, 155.0, 150.0, 120.0, 105.0, 110.0, 115.0, 125.0, 130.0, 135.0]},
        cloud_cover_metadata={"average_oktas": 4},
        rainfall_metadata={"annual_mm": 970.0},
        heating_degree_days=80.0,
        cooling_degree_days=1050.0,
        climate_zone="Warm Humid",
        weather_file_metadata={"format": "metadata-only", "source": "workspace"},
    )
    wall = simulation.create_energy_envelope_element(
        study,
        "External Walls",
        "Wall",
        area=260.0,
        material_references=[{"material_id": wall_material.id, "thermal_properties_id": wall_thermal.id}],
        geometry_references=[{"body_id": "office-envelope", "face_group": "walls"}],
        zone_id="office-zone",
        orientation={"azimuths": [0.0, 90.0, 180.0, 270.0]},
    )
    window = simulation.create_energy_envelope_element(
        study,
        "South Windows",
        "Window",
        area=18.0,
        u_value=2.0,
        material_references=[{"material_id": glazing.id, "thermal_properties_id": glazing_thermal.id}],
        shading_metadata={"overhang_depth": 0.6, "transmittance": 0.68},
        geometry_references=[{"face_id": "south-window"}],
        zone_id="office-zone",
        orientation={"azimuth": 180.0, "tilt": 90.0},
        metadata={"transmittance": 0.68},
    )
    floor = simulation.create_energy_envelope_element(
        study,
        "Office Floor",
        "Floor",
        area=120.0,
        u_value=0.35,
        geometry_references=[{"face_id": "office-floor"}],
        zone_id="office-zone",
    )
    roof = simulation.create_energy_envelope_element(
        study,
        "Office Roof",
        "Roof",
        area=120.0,
        u_value=0.3,
        geometry_references=[{"face_id": "office-roof"}],
        zone_id="office-zone",
    )

    simulation.create_energy_schedule(study, "Occupancy Weekday", "Occupancy", values=[550.0] * 12, gains={"load_factor": 0.55})
    simulation.create_energy_schedule(study, "Lighting Schedule", "Lighting", values=[900.0] * 12, gains={"load_factor": 0.45})
    simulation.create_energy_schedule(study, "Equipment Schedule", "Equipment", values=[1200.0] * 12, gains={"load_factor": 0.5})
    simulation.create_energy_schedule(study, "Ventilation Schedule", "Ventilation", values=[1.0] * 12, gains={"air_change_watts_per_k": 14.0})
    simulation.create_hvac_system(study, "VRF Heat Pump Heating", "Heating System", efficiency=3.2, capacity=18.0)
    simulation.create_hvac_system(study, "VRF Heat Pump Cooling", "Cooling System", efficiency=3.8, capacity=22.0)
    simulation.create_hvac_system(study, "Fresh Air Unit", "Ventilation System", efficiency=0.82, capacity=6.0)

    assert climate.climate_zone == "Warm Humid"
    assert wall.area == 260.0
    assert window.shading_metadata["overhang_depth"] == 0.6
    assert floor.element_type == "Floor"
    assert roof.element_type == "Roof"
    assert len(simulation.daylight_openings) == 1

    command = RunEnergyStudyCommand(workspace, study)
    workspace.command_manager.execute(command)

    result = simulation.results[-1]
    report = result.reports[0]
    assert study.status == "Solved"
    assert result.result_type == "Whole-Building Energy Result"
    assert result.scalars["annual_energy_use"] > 0.0
    assert result.scalars["energy_use_intensity"] > 0.0
    assert result.scalars["peak_cooling"] > 0.0
    assert "monthly_profiles" in result.vectors
    assert len(result.statistics["monthly_profiles"]) == 12
    assert result.statistics["window_to_wall_ratio"] > 0.0
    assert result.statistics["operational_carbon"] > 0.0
    assert report["climate_summary"]["climate_zone"] == "Warm Humid"
    assert report["performance_rating"] in {"High Performance", "Efficient", "Needs Improvement", "High Energy Demand"}
    assert result.metadata["thermal_reuse"] is True
    assert result.metadata["daylight_reuse"] is True
    assert simulation.visualizations[-1].display_settings["energy_dashboard"] is True
    assert simulation.energy_execution_history[-1].status == "Completed"

    workspace.command_manager.undo()
    assert workspace.simulation_workspace.results == []
    workspace.command_manager.redo()
    assert len(workspace.simulation_workspace.results) == 1

    with TemporaryDirectory() as directory:
        path = Path(directory) / "energy_analysis.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.simulation_workspace.load_from_settings()
    restored_simulation = restored.simulation_workspace
    assert len(restored_simulation.energy_climate_profiles) == 1
    assert len(restored_simulation.energy_envelope_elements) == 4
    assert len(restored_simulation.energy_schedules) == 4
    assert len(restored_simulation.hvac_systems) == 3
    assert len(restored_simulation.energy_execution_history) == 1
    assert len(restored_simulation.results) == 1
    assert restored_simulation.diagnostics().to_dict()["statistics"]["energy_solved_studies"] == 1

    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []


if __name__ == "__main__":
    test_energy_analysis_foundation_solver_reports_visualization_and_persistence()
    print("energy-analysis-foundation-ok")

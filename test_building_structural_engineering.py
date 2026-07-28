from pathlib import Path
from tempfile import TemporaryDirectory

from engine.commands.structural_simulation_command import RunBuildingStructuralStudyCommand
from engine.product import EngineeringMaterial
from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_building_structural_engineering_reuses_structural_solver_and_persists():
    workspace = Workspace("Building Structural Project")
    simulation = workspace.simulation_workspace.initialize()

    steel = workspace.product_manager.engineering_material_manager.add_item(
        EngineeringMaterial("Building Steel", density=7850.0)
    )
    properties = simulation.register_material_properties(
        steel,
        density=7850.0,
        elastic_modulus=200_000_000_000.0,
        poisson_ratio=0.30,
        yield_strength=250_000_000.0,
        ultimate_strength=400_000_000.0,
    )
    project = simulation.create_project("Tower Frame", "Release 1.8 Batch C")
    study = simulation.create_building_structural_study(
        project,
        "Tower Lateral Study",
        "Two Storey Steel Frame",
        storeys=[
            {"name": "Ground", "elevation": 0.0, "height": 0.0, "node_ids": ["n1", "n2"]},
            {"name": "Level 1", "elevation": 3.0, "height": 3.0, "node_ids": ["n3"]},
        ],
        target_geometry=[{"assembly_id": "building-frame"}],
        solver_settings={"analysis_type": "Building Linear Static"},
        visualization_settings={"building_drift": True},
    )
    fixed = simulation.create_boundary_condition("Base Fixed", "Fixed", [{"node_id": "n1"}])
    roller = simulation.create_boundary_condition("Base Roller", "Roller", [{"node_id": "n2"}], {"axes": ["y", "z"]})
    floor_z = simulation.create_boundary_condition("Planar Floor", "Roller", [{"node_id": "n3"}], {"axes": ["z"]})
    study.boundary_condition_ids.extend([fixed.id, roller.id, floor_z.id])

    column = simulation.register_steel_member(
        study,
        "C1",
        "Steel Column",
        {"area": 0.02, "section_name": "UC"},
        "Level 1",
        [{"body_id": "column-body"}],
        {"id": "n2", "x": 4.0, "y": 0.0, "z": 0.0},
        {"id": "n3", "x": 4.0, "y": 3.0, "z": 0.0},
        steel,
        connection_metadata={"base_plate": "pinned"},
        steel_metadata={"grade": "S275"},
    )
    beam = simulation.register_steel_member(
        study,
        "B1",
        "Steel Beam",
        {"area": 0.015, "section_name": "UB"},
        "Ground",
        [{"body_id": "beam-body"}],
        {"id": "n1", "x": 0.0, "y": 0.0, "z": 0.0},
        {"id": "n2", "x": 4.0, "y": 0.0, "z": 0.0},
        steel,
    )
    brace = simulation.register_steel_member(
        study,
        "BR1",
        "Steel Bracing",
        {"area": 0.01, "section_name": "CHS"},
        "Level 1",
        [{"body_id": "brace-body"}],
        {"id": "n1", "x": 0.0, "y": 0.0, "z": 0.0},
        {"id": "n3", "x": 4.0, "y": 3.0, "z": 0.0},
        steel,
    )
    system = simulation.create_building_structural_system(
        study,
        "Primary Braced Frame",
        "Braced Frame",
        [column.id, beam.id, brace.id],
        {"lateral_system": True},
    )
    load = simulation.create_building_load(
        study,
        "Level Wind",
        "Wind Load",
        "Point",
        [{"node_id": "n3"}],
        {"vector": {"x": 1000.0, "y": 0.0, "z": 0.0}},
        "Level 1",
    )
    code = simulation.register_design_code(
        "IS 875",
        load_factors={"wind": 1.5},
        partial_safety_factors={"steel": 1.1},
        combination_rules={"service": [load.id]},
    )
    simulation.assign_structural_material(study, steel, "Assembly", [{"assembly_id": "building-frame"}], properties)

    assert system.system_type == "Braced Frame"
    assert code.name == "IS 875"
    assert load.load_case_id in study.load_case_ids

    command = RunBuildingStructuralStudyCommand(workspace, study)
    workspace.command_manager.execute(command)

    result = simulation.results[-1]
    building = result.metadata["building"]
    report = result.reports[-1]
    assert study.status == "Solved"
    assert simulation.building_structural_studies[0].status == "Solved"
    assert building["statistics"]["building"]["member_count"] == 3
    assert building["statistics"]["building"]["truss_analysis"] is True
    assert building["statistics"]["building"]["beam_analysis"] is True
    assert building["statistics"]["building"]["column_analysis"] is True
    assert building["statistics"]["maximum_drift"] >= 0.0
    assert report["structural_system_summary"][0]["system_type"] == "Braced Frame"
    assert simulation.visualizations[-1].display_settings["building_visualization"] is True
    assert workspace.command_manager.undo_count == 1

    workspace.command_manager.undo()
    assert workspace.simulation_workspace.results == []
    workspace.command_manager.redo()
    assert len(workspace.simulation_workspace.results) == 1

    with TemporaryDirectory() as directory:
        path = Path(directory) / "building_structural.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored.simulation_workspace.load_from_settings()
    restored_simulation = restored.simulation_workspace
    assert len(restored_simulation.building_structural_studies) == 1
    assert len(restored_simulation.building_members) == 3
    assert len(restored_simulation.building_systems) == 1
    assert len(restored_simulation.building_loads) == 1
    assert len(restored_simulation.engineering_design_codes) == 1
    assert len(restored_simulation.results) == 1
    assert restored_simulation.diagnostics().to_dict()["statistics"]["building_members"] == 3

    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []


if __name__ == "__main__":
    test_building_structural_engineering_reuses_structural_solver_and_persists()
    print("building-structural-engineering-ok")

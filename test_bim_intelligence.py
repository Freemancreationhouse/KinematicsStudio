from engine.bim import BIMParametricDefinition, BIMProject
from engine.commands import (
    AddBIMDigitalTwinRecordCommand,
    AddBIMIntelligenceIssueCommand,
    AddBIMReviewSessionCommand,
    AddBIMRuleCommand,
    CreateColumnCommand,
    CreateDoorCommand,
    CreateWallCommand,
    GenerateAIBIMRecommendationsCommand,
    HostDoorByWallCommand,
    RunBIMClashDetectionCommand,
    RunBIMModelValidationCommand,
    RunBIMRuleCheckCommand,
    ValidateBIMIntelligenceCommand,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.bim_manager
manager.initialize(
    "Release 1.9 BIM Intelligence",
    project_units="meters",
    preferences={"energy_review": True},
)

project_node = manager.create_spatial_element("Project", "Intelligence Project")
site = manager.create_spatial_element("Site", "Main Site", project_node.id)
building = manager.create_spatial_element("Building", "Coordination Tower", site.id)
level = manager.create_spatial_element("Building Storey", "Level 01", building.id)
room = manager.create_spatial_element("Space", "Lobby", level.id)
manager.create_spatial_element("Space", "Lobby", level.id)

wall_type = manager.create_native_element_type(
    "Wall Type 100",
    "Wall",
    "Architecture",
    material_id="mat-concrete",
    parameters=BIMParametricDefinition(thickness=0.1, height=3.2, length=6.0),
)
column_type = manager.create_native_element_type(
    "Column Type 300",
    "Column",
    "Structure",
    material_id="mat-steel",
    parameters=BIMParametricDefinition(width=0.3, length=0.3, height=3.2),
)

wall_body = {"body_id": "body-intel-wall", "body_name": "Parametric wall body", "source": "BodyManager"}
workspace.command_manager.execute(
    CreateWallCommand(
        workspace,
        "Wall Lobby 01",
        [wall_body],
        element_type_id=wall_type.id,
        material_assignment_id="mat-concrete",
        level_id=level.id,
        parameters=BIMParametricDefinition(thickness=0.1, height=3.2, length=6.0),
    )
)
wall = manager.active_project.native_elements[-1]

workspace.command_manager.execute(
    CreateWallCommand(
        workspace,
        "Wall Lobby 01",
        [wall_body],
        element_type_id=wall_type.id,
        material_assignment_id="mat-concrete",
        level_id=level.id,
        parameters=BIMParametricDefinition(thickness=0.2, height=3.2, length=6.0),
    )
)
duplicate_wall = manager.active_project.native_elements[-1]

workspace.command_manager.execute(
    CreateDoorCommand(
        workspace,
        "Door Lobby 01",
        [{"body_id": "body-door-01", "body_name": "Parametric door body", "source": "BodyManager"}],
        element_type_id="",
        material_assignment_id="mat-wood",
        level_id=level.id,
        host_id=wall.id,
        parameters=BIMParametricDefinition(width=0.9, height=2.1),
    )
)
door = manager.active_project.native_elements[-1]

workspace.command_manager.execute(
    CreateColumnCommand(
        workspace,
        "Column Grid A1",
        [{"body_id": "body-column-a1", "body_name": "Parametric column body", "source": "BodyManager"}],
        element_type_id=column_type.id,
        material_assignment_id="mat-steel",
        level_id=level.id,
        parameters=BIMParametricDefinition(width=0.3, length=0.3, height=3.2),
    )
)
column = manager.active_project.native_elements[-1]

workspace.command_manager.execute(
    HostDoorByWallCommand(
        workspace,
        door.id,
        wall.id,
        opening_metadata={"opening_body_id": "opening-lobby-01"},
    )
)
workspace.command_manager.execute(
    HostDoorByWallCommand(
        workspace,
        door.id,
        duplicate_wall.id,
        opening_metadata={"opening_body_id": "opening-lobby-01"},
    )
)

manager.create_classification_assignment("Uniclass", "Ss_25_10", "Walls", target_id=wall.id)
manager.create_classification_assignment("Uniclass", "Ss_25_30", "Doors", target_id=door.id)

workspace.command_manager.execute(
    AddBIMRuleCommand(
        workspace,
        "Wall naming standard",
        "Naming",
        "Wall",
        {"starts_with": "Wall"},
        "Medium",
    )
)
workspace.command_manager.execute(RunBIMRuleCheckCommand(workspace))
rule_results = manager.active_project.intelligence_rule_results
assert rule_results and all(result.passed for result in rule_results), [result.message for result in rule_results]

workspace.command_manager.execute(RunBIMClashDetectionCommand(workspace, ["Architecture"], clearance=0.05))
clash_types = {clash.clash_type for clash in manager.active_project.intelligence_clashes}
assert {"Hard Clash", "Duplicate Element", "Duplicate Opening"}.issubset(clash_types)

workspace.command_manager.execute(RunBIMModelValidationCommand(workspace))
model_validation = manager.active_project.intelligence_validation_report
assert model_validation.valid, model_validation.issues
assert any("Duplicate room" in warning for warning in model_validation.warnings)

manual_issue = AddBIMIntelligenceIssueCommand(
    workspace,
    "Coordination",
    "Review lobby wall duplicate",
    description="Duplicate wall reference requires design review.",
    severity="High",
    element_ids=[wall.id, duplicate_wall.id],
    priority="High",
    snapshots=[{"view": "3D Coordination", "room_id": room.id}],
    clash_ids=[manager.active_project.intelligence_clashes[0].id],
)
workspace.command_manager.execute(manual_issue)
issue = manual_issue.issue
workspace.command_manager.execute(
    AddBIMReviewSessionCommand(
        workspace,
        "Lobby Coordination Review",
        "BIM Coordinator",
        [issue.id],
        [{"view": "3D Coordination", "issue_id": issue.id}],
    )
)

workspace.command_manager.execute(
    AddBIMDigitalTwinRecordCommand(
        workspace,
        wall.id,
        asset_metadata={"asset_tag": "W-L01-001"},
        maintenance_metadata={"inspection_cycle": "annual"},
        sensor_metadata={"planned_sensors": ["temperature"], "live_connection": False},
        facility_metadata={"zone": "Lobby"},
    )
)

workspace.command_manager.execute(GenerateAIBIMRecommendationsCommand(workspace))
recommendations = manager.active_project.intelligence_recommendations
assert recommendations
assert all(item.command_plan for item in recommendations)
assert {step["command"] for item in recommendations for step in item.command_plan}.issubset(
    {
        "EditBIMElementCommand",
        "GenerateBIMDrawingCommand",
        "RunBIMModelValidationCommand",
    }
)
assert wall.parameters.thickness == 0.1

workspace.command_manager.execute(ValidateBIMIntelligenceCommand(workspace))
validation = manager.active_project.intelligence_validation_report
diagnostics = manager.bim_intelligence_diagnostics_report()
visualization = manager.bim_intelligence_visualization_metadata()

assert validation.valid, validation.issues
assert diagnostics.clashes >= 3
assert diagnostics.issues >= 4
assert diagnostics.recommendations >= 3
assert diagnostics.digital_twins == 1
assert visualization["clash_visualization"]
assert visualization["issue_highlighting"]
assert visualization["ai_suggestion_overlays"]
assert visualization["digital_twin_metadata"]
assert workspace.scene3d.entities() == []
assert workspace.command_manager.undo_count >= 12

workspace.command_manager.undo()
assert manager.active_project.intelligence_validation_report is not validation
workspace.command_manager.redo()
assert manager.active_project.intelligence_validation_report.valid

persisted = manager.to_dict()
restored = manager.__class__()
restored.from_dict(persisted)
assert isinstance(restored.active_project, BIMProject)
restored_validation = restored.validate_bim_intelligence()

assert restored_validation.valid, restored_validation.issues
assert len(restored.active_project.intelligence_clashes) >= 3
assert len(restored.active_project.intelligence_recommendations) >= 3
assert restored.active_project.digital_twin_records[0].target_id == wall.id

print("bim-intelligence-ok")

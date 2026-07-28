import json
from pathlib import Path

from engine.commands import (
    AddDesignReviewCheckpointCommand,
    AddEntityCommand,
    AddParcelCommand,
    AddRoadCommand,
    AddSiteBoundaryCommand,
    AddUtilityNetworkCommand,
    AnalyzeSiteDrainageCommand,
    CreateAISiteIntelligenceProjectCommand,
    CreateBIMProjectCommand,
    CreateCoordinationIssueCommand,
    CreateDataExchangeSessionCommand,
    CreateDesignApprovalSessionCommand,
    CreateDesignReviewSessionCommand,
    CreateGISProjectCommand,
    CreateInfrastructureProjectCommand,
    CreateSiteEngineeringProjectCommand,
    CreateTerrainProjectCommand,
    CreateWorkflowSessionCommand,
    ExecuteWorkflowSessionCommand,
    GenerateAISiteEngineeringReportsCommand,
    GenerateDesignCoordinationVisualizationCommand,
    ImportGISFileCommand,
    ImportTerrainFileCommand,
    InitializeDataExchangeManagerCommand,
    InitializeDesignCoordinationCommand,
    InitializeIntegratedDesignPlatformCommand,
    InitializeWorkflowOrchestratorCommand,
    RecordDesignApprovalDecisionCommand,
    RunBuildabilityAnalysisCommand,
    RunConstraintIntelligenceCommand,
    RunDesignClashDetectionCommand,
    RunEnvironmentalAnalysisCommand,
    RunIntegratedDesignRegressionCommand,
    RunSitePlanningCommand,
    SynchronizeDataExchangeCommand,
    UpdateCoordinationIssueCommand,
    ValidateDesignCoordinationCommand,
)
from engine.entities import LineEntity
from engine.geometry import Vector2
from engine.storage.project import ProjectSerializer
from engine.workspace.workspace import Workspace


tmp_dir = Path(".tmp_test_output/design_coordination")
tmp_dir.mkdir(parents=True, exist_ok=True)

terrain_path = tmp_dir / "coordination_surface.asc"
terrain_path.write_text(
    "\n".join(
        [
            "ncols 4",
            "nrows 4",
            "xllcorner 0",
            "yllcorner 0",
            "cellsize 10",
            "NODATA_value -9999",
            "30 29 28 27",
            "29 28 27 26",
            "28 27 26 25",
            "27 26 25 24",
        ]
    ),
    encoding="utf-8",
)

geojson_path = tmp_dir / "coordination_site.geojson"
geojson_path.write_text(
    json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "Coordination Wall", "parcel": "primary"},
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [28, 0], [28, 28], [0, 28], [0, 0]]]},
                },
                {
                    "type": "Feature",
                    "properties": {"name": "Coordination Access", "highway": "service"},
                    "geometry": {"type": "LineString", "coordinates": [[-4, 14], [14, 14], [34, 14]]},
                },
            ],
        }
    ),
    encoding="utf-8",
)

workspace = Workspace()
workspace.command_manager.execute(AddEntityCommand(workspace.entities, LineEntity(Vector2(0, 0), Vector2(16, 0))))
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Coordination BIM", metadata={"release": "2.1"}))
workspace.bim_manager.initialize("Coordination BIM", project_units="meters")
storey = workspace.bim_manager.create_spatial_element("Building Storey", "Coordination Level", elevation=0.0)
wall = workspace.bim_manager.create_building_object(
    "Coordination Wall",
    "Wall",
    [{"body_id": "body-coordination-wall", "source": "BodyManager"}],
    spatial_container_id=storey.id,
)
workspace.bim_manager.create_bim_relationship("Contains", storey.id, [wall.id])

CreateGISProjectCommand(workspace, "Coordination GIS").execute()
ImportGISFileCommand(workspace, geojson_path, "Coordination Wall").execute()
CreateTerrainProjectCommand(workspace, "Coordination Terrain").execute()
terrain_import = ImportTerrainFileCommand(workspace, terrain_path, "Coordination Terrain Surface")
terrain_import.execute()
surface = terrain_import.surface
CreateSiteEngineeringProjectCommand(workspace, "Coordination Site").execute()
AddSiteBoundaryCommand(workspace, "Coordination Limit", "Construction Limit", [[0, 0], [28, 0], [28, 28], [0, 28]]).execute()
AnalyzeSiteDrainageCommand(workspace, surface, "Coordination Drainage").execute()
CreateInfrastructureProjectCommand(workspace, "Coordination Infrastructure").execute()
AddRoadCommand(workspace, "Coordination Access", [[-4, 14], [14, 14], [34, 14]], hierarchy="Collector").execute()
AddParcelCommand(workspace, "Coordination Parcel", [[0, 0], [28, 0], [28, 28], [0, 28]], {"parcel": "coordination"}, {"owner": "Workspace"}, {"phase": "review"}).execute()
AddUtilityNetworkCommand(workspace, "Water", "Coordination Water", nodes=[{"id": "W1", "point": [0, 0]}, {"id": "W2", "point": [28, 28]}], edges=[{"from": "W1", "to": "W2"}]).execute()
CreateAISiteIntelligenceProjectCommand(workspace, "Coordination Intelligence", settings={"maximum_buildable_slope": 6.0, "preferred_buildable_slope": 1.5}).execute()
RunBuildabilityAnalysisCommand(workspace, surface).execute()
RunEnvironmentalAnalysisCommand(workspace, surface).execute()
RunConstraintIntelligenceCommand(workspace, surface).execute()
RunSitePlanningCommand(workspace, surface).execute()
GenerateAISiteEngineeringReportsCommand(workspace).execute()

workspace.command_manager.execute(InitializeIntegratedDesignPlatformCommand(workspace, "Design Coordination Integrated Project", "Release 2.1 Batch D"))
workspace.command_manager.execute(InitializeWorkflowOrchestratorCommand(workspace))
workflow = CreateWorkflowSessionCommand(workspace, "Site to Building Coordination", "Design Coordination Workflow", {"objective": "review clashes"})
workspace.command_manager.execute(workflow)
workspace.command_manager.execute(ExecuteWorkflowSessionCommand(workspace, workflow.session.id))

workspace.command_manager.execute(InitializeDataExchangeManagerCommand(workspace))
exchange = CreateDataExchangeSessionCommand(workspace, "Coordination Exchange")
workspace.command_manager.execute(exchange)
workspace.command_manager.execute(SynchronizeDataExchangeCommand(workspace, exchange.session.id))

initialize_coordination = InitializeDesignCoordinationCommand(workspace)
workspace.command_manager.execute(initialize_coordination)
assert initialize_coordination.state["uses_existing_project_model"] is True
assert initialize_coordination.state["geometry_owned_by_coordination"] is False

clash_detection = RunDesignClashDetectionCommand(workspace)
workspace.command_manager.execute(clash_detection)
coordination = workspace.integrated_design_manager.design_coordination_manager
assert isinstance(clash_detection.clashes, list)
assert coordination.clash_registry
assert any(item.clash_type in {"Hard Clash", "Duplicate Object", "Reference Inconsistency", "Disconnected System", "Cross-Discipline Conflict"} for item in coordination.clash_registry.values())
first_clash = next(iter(coordination.clash_registry.values()))

issue_command = CreateCoordinationIssueCommand(
    workspace,
    "Resolve coordination conflict",
    first_clash.clash_type,
    first_clash.severity,
    "High",
    first_clash.linked_objects,
    [first_clash.id],
    assigned_to="Coordination Lead",
    comments=["Review source and target references"],
)
workspace.command_manager.execute(issue_command)
assert issue_command.issue.id in coordination.issue_registry
assert coordination.issue_registry[issue_command.issue.id].assigned_to == "Coordination Lead"

update_issue = UpdateCoordinationIssueCommand(
    workspace,
    issue_command.issue.id,
    status="In Review",
    comment="Reviewed during multidisciplinary coordination.",
)
workspace.command_manager.execute(update_issue)
assert coordination.issue_registry[issue_command.issue.id].status == "In Review"

review_command = CreateDesignReviewSessionCommand(
    workspace,
    "Batch D Design Review",
    reviewer="Lead Engineer",
    issue_ids=[issue_command.issue.id],
    clash_ids=[first_clash.id],
)
workspace.command_manager.execute(review_command)
workspace.command_manager.execute(AddDesignReviewCheckpointCommand(workspace, review_command.session.id, "Review completed", decision="Proceed to approval", reviewer="Lead Engineer"))
assert coordination.review_sessions[-1].decision_tracking

approval_command = CreateDesignApprovalSessionCommand(workspace, "Batch D Approval", approver="Chief Engineer", issue_ids=[issue_command.issue.id])
workspace.command_manager.execute(approval_command)
workspace.command_manager.execute(RecordDesignApprovalDecisionCommand(workspace, approval_command.session.id, "Approved", reviewer="Chief Engineer", metadata={"basis": "coordination review"}))
assert coordination.approval_sessions[-1].status == "Approved"

validation = ValidateDesignCoordinationCommand(workspace)
workspace.command_manager.execute(validation)
assert validation.report["valid"] is True, validation.report
assert validation.report["statistics"]["persistence"]["passed"] is True
assert validation.report["statistics"]["summary"]["geometry_owned_by_coordination"] is False

visual = GenerateDesignCoordinationVisualizationCommand(workspace)
workspace.command_manager.execute(visual)
for key in ("clash_overlays", "issue_overlays", "review_overlays", "approval_overlays", "coordination_overlays", "validation_overlays", "diagnostics"):
    assert key in visual.metadata

regression = RunIntegratedDesignRegressionCommand(workspace)
workspace.command_manager.execute(regression)
assert regression.result["passed"] is True
assert {item["name"] for item in regression.result["checks"]} >= {
    "Design Coordination Manager",
    "Clash Registry",
    "Issue Registry",
    "Review Sessions",
    "Approval Sessions",
    "Production Clash Detection",
    "Coordination Intelligence",
    "Coordination Persistence",
    "Coordination Diagnostics",
}

undo_count = workspace.command_manager.undo_count
workspace.command_manager.undo()
assert workspace.command_manager.undo_count == undo_count - 1
workspace.command_manager.redo()
assert workspace.command_manager.undo_count == undo_count

serializer = ProjectSerializer()
project_path = tmp_dir / "design_coordination_project.json"
serializer.save(workspace, project_path)
restored = serializer.load(project_path)
restored_coordination = restored.integrated_design_manager.design_coordination_manager
assert restored_coordination.clash_registry
assert restored_coordination.issue_registry
assert restored_coordination.review_sessions
assert restored_coordination.approval_sessions
assert restored_coordination.coordination_summary()["geometry_owned_by_coordination"] is False

print("clash-detection-design-coordination-ok")

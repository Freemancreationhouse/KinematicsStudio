import json
from pathlib import Path

from engine.commands import (
    AddEntityCommand,
    AddParcelCommand,
    AddRoadCommand,
    AddSiteBoundaryCommand,
    AddUtilityNetworkCommand,
    AnalyzeSiteDrainageCommand,
    CoordinateAITaskCommand,
    CreateAISiteIntelligenceProjectCommand,
    CreateAutomationSessionCommand,
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
    ExecuteAutomationSessionCommand,
    ExecuteWorkflowSessionCommand,
    GenerateAISiteEngineeringReportsCommand,
    GenerateAutomationAIVisualizationCommand,
    ImportGISFileCommand,
    ImportTerrainFileCommand,
    InitializeAutomationAICoordinationCommand,
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
    ValidateAutomationAICoordinationCommand,
)
from engine.entities import LineEntity
from engine.geometry import Vector2
from engine.storage.project import ProjectSerializer
from engine.workspace.workspace import Workspace


tmp_dir = Path(".tmp_test_output/automation_ai_coordination")
tmp_dir.mkdir(parents=True, exist_ok=True)

terrain_path = tmp_dir / "automation_surface.asc"
terrain_path.write_text(
    "\n".join(
        [
            "ncols 4",
            "nrows 4",
            "xllcorner 0",
            "yllcorner 0",
            "cellsize 10",
            "NODATA_value -9999",
            "31 30 29 28",
            "30 29 28 27",
            "29 28 27 26",
            "28 27 26 25",
        ]
    ),
    encoding="utf-8",
)

geojson_path = tmp_dir / "automation_site.geojson"
geojson_path.write_text(
    json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "Automation Wall", "parcel": "primary"},
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [32, 0], [32, 32], [0, 32], [0, 0]]]},
                },
                {
                    "type": "Feature",
                    "properties": {"name": "Automation Access", "highway": "service"},
                    "geometry": {"type": "LineString", "coordinates": [[-4, 16], [16, 16], [36, 16]]},
                },
            ],
        }
    ),
    encoding="utf-8",
)

workspace = Workspace()
workspace.command_manager.execute(AddEntityCommand(workspace.entities, LineEntity(Vector2(0, 0), Vector2(18, 0))))
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Automation BIM", metadata={"release": "2.1"}))
workspace.bim_manager.initialize("Automation BIM", project_units="meters")
storey = workspace.bim_manager.create_spatial_element("Building Storey", "Automation Level", elevation=0.0)
wall = workspace.bim_manager.create_building_object(
    "Automation Wall",
    "Wall",
    [{"body_id": "body-automation-wall", "source": "BodyManager"}],
    spatial_container_id=storey.id,
)
workspace.bim_manager.create_bim_relationship("Contains", storey.id, [wall.id])

CreateGISProjectCommand(workspace, "Automation GIS").execute()
ImportGISFileCommand(workspace, geojson_path, "Automation Wall").execute()
CreateTerrainProjectCommand(workspace, "Automation Terrain").execute()
terrain_import = ImportTerrainFileCommand(workspace, terrain_path, "Automation Terrain Surface")
terrain_import.execute()
surface = terrain_import.surface
CreateSiteEngineeringProjectCommand(workspace, "Automation Site").execute()
AddSiteBoundaryCommand(workspace, "Automation Limit", "Construction Limit", [[0, 0], [32, 0], [32, 32], [0, 32]]).execute()
AnalyzeSiteDrainageCommand(workspace, surface, "Automation Drainage").execute()
CreateInfrastructureProjectCommand(workspace, "Automation Infrastructure").execute()
AddRoadCommand(workspace, "Automation Access", [[-4, 16], [16, 16], [36, 16]], hierarchy="Collector").execute()
AddParcelCommand(workspace, "Automation Parcel", [[0, 0], [32, 0], [32, 32], [0, 32]], {"parcel": "automation"}, {"owner": "Workspace"}, {"phase": "automation"}).execute()
AddUtilityNetworkCommand(workspace, "Water", "Automation Water", nodes=[{"id": "W1", "point": [0, 0]}, {"id": "W2", "point": [32, 32]}], edges=[{"from": "W1", "to": "W2"}]).execute()
CreateAISiteIntelligenceProjectCommand(workspace, "Automation Intelligence", settings={"maximum_buildable_slope": 6.0, "preferred_buildable_slope": 1.5}).execute()
RunBuildabilityAnalysisCommand(workspace, surface).execute()
RunEnvironmentalAnalysisCommand(workspace, surface).execute()
RunConstraintIntelligenceCommand(workspace, surface).execute()
RunSitePlanningCommand(workspace, surface).execute()
GenerateAISiteEngineeringReportsCommand(workspace).execute()

workspace.command_manager.execute(InitializeIntegratedDesignPlatformCommand(workspace, "Automation Integrated Project", "Release 2.1 Batch E"))
workspace.command_manager.execute(InitializeWorkflowOrchestratorCommand(workspace))
workflow = CreateWorkflowSessionCommand(workspace, "Site to Building Coordination", "Automation Workflow", {"objective": "automate multidisciplinary review"})
workspace.command_manager.execute(workflow)
workspace.command_manager.execute(ExecuteWorkflowSessionCommand(workspace, workflow.session.id))

workspace.command_manager.execute(InitializeDataExchangeManagerCommand(workspace))
exchange = CreateDataExchangeSessionCommand(workspace, "Automation Exchange")
workspace.command_manager.execute(exchange)
workspace.command_manager.execute(SynchronizeDataExchangeCommand(workspace, exchange.session.id))

workspace.command_manager.execute(InitializeDesignCoordinationCommand(workspace))
clash_detection = RunDesignClashDetectionCommand(workspace)
workspace.command_manager.execute(clash_detection)
coordination = workspace.integrated_design_manager.design_coordination_manager
first_clash = next(iter(coordination.clash_registry.values()))
issue = CreateCoordinationIssueCommand(workspace, "Automation coordination issue", first_clash.clash_type, first_clash.severity, "High", first_clash.linked_objects, [first_clash.id])
workspace.command_manager.execute(issue)
review = CreateDesignReviewSessionCommand(workspace, "Automation Review", issue_ids=[issue.issue.id], clash_ids=[first_clash.id])
workspace.command_manager.execute(review)
approval = CreateDesignApprovalSessionCommand(workspace, "Automation Approval", issue_ids=[issue.issue.id])
workspace.command_manager.execute(approval)
workspace.command_manager.execute(RecordDesignApprovalDecisionCommand(workspace, approval.session.id, "Approved", reviewer="Automation Lead"))

initialize_automation = InitializeAutomationAICoordinationCommand(workspace)
workspace.command_manager.execute(initialize_automation)
automation = workspace.integrated_design_manager.automation_ai_coordination_manager
assert initialize_automation.registry
assert automation.automation_scheduler["status"] == "Ready"
assert automation.ai_coordination_context["duplicate_ai_engine"] is False

custom_tasks = [
    {"name": "Validate shared data", "discipline": "GIS", "action": "Validate synchronized references", "priority": 70, "condition": {"data_exchange_status": "Synchronized"}},
    {"name": "Review coordination issues", "discipline": "BIM", "action": "Review open design issues", "priority": 90, "condition": {"minimum_clashes": 1}},
    {"name": "Summarize automation readiness", "discipline": "AI Studio", "action": "Summarize recommendations", "priority": 60},
]
session_command = CreateAutomationSessionCommand(workspace, "Batch E Automation Session", tasks=custom_tasks, ai_objective="Coordinate engineering automation")
workspace.command_manager.execute(session_command)
session = session_command.session
assert session.status == "Ready"
assert len(session.tasks) == 3
assert len(session.execution_queue) == 3
assert session.recommendations

execute = ExecuteAutomationSessionCommand(workspace, session.id)
workspace.command_manager.execute(execute)
assert execute.result.status == "Completed"
assert execute.result.result_tracking["geometry_modified"] is False
assert execute.result.execution_history

ai_task = CoordinateAITaskCommand(workspace, "Explain automation readiness from existing coordination data", metadata={"release": "2.1", "batch": "E"})
workspace.command_manager.execute(ai_task)
assert ai_task.entry["duplicate_ai_engine"] is False
assert automation.prompt_history

validation = ValidateAutomationAICoordinationCommand(workspace, session.id)
workspace.command_manager.execute(validation)
assert validation.report["valid"] is True, validation.report
assert validation.report["statistics"]["persistence"]["passed"] is True
assert validation.report["statistics"]["ai_context"]["duplicate_ai_engine"] is False

visual = GenerateAutomationAIVisualizationCommand(workspace)
workspace.command_manager.execute(visual)
for key in ("automation_overlays", "execution_overlays", "ai_activity_overlays", "workflow_overlays", "recommendation_overlays", "validation_overlays", "diagnostics"):
    assert key in visual.metadata

regression = RunIntegratedDesignRegressionCommand(workspace)
workspace.command_manager.execute(regression)
assert regression.result["passed"] is True
assert {item["name"] for item in regression.result["checks"]} >= {
    "Automation & AI Coordination Manager",
    "Automation Registry",
    "Automation Scheduler",
    "Execution Queue",
    "AI Coordination",
    "Recommendation Metadata",
    "Automation Diagnostics",
    "Automation Persistence",
}

undo_count = workspace.command_manager.undo_count
workspace.command_manager.undo()
assert workspace.command_manager.undo_count == undo_count - 1
workspace.command_manager.redo()
assert workspace.command_manager.undo_count == undo_count

serializer = ProjectSerializer()
project_path = tmp_dir / "automation_ai_coordination_project.json"
serializer.save(workspace, project_path)
restored = serializer.load(project_path)
restored_automation = restored.integrated_design_manager.automation_ai_coordination_manager
assert restored_automation.automation_sessions
assert restored_automation.automation_registry
assert restored_automation.execution_history
assert restored_automation.prompt_history
assert restored_automation.ai_coordination_context["duplicate_ai_engine"] is False

print("multi-discipline-automation-ai-coordination-ok")

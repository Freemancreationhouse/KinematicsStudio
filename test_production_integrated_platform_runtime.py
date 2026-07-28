import json
from pathlib import Path

from engine.commands import (
    AddEntityCommand,
    AddParcelCommand,
    AddRoadCommand,
    AddSiteBoundaryCommand,
    AddUtilityNetworkCommand,
    AnalyzeSiteDrainageCommand,
    BootstrapIntegratedPlatformRuntimeCommand,
    CertifyIntegratedPlatformRuntimeCommand,
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
    GenerateIntegratedPlatformRuntimeVisualizationCommand,
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
    ShutdownIntegratedPlatformRuntimeCommand,
    StartupIntegratedPlatformRuntimeCommand,
    SynchronizeDataExchangeCommand,
    ValidateIntegratedPlatformRuntimeCommand,
)
from engine.entities import LineEntity
from engine.geometry import Vector2
from engine.storage.project import ProjectSerializer
from engine.workspace.workspace import Workspace


tmp_dir = Path(".tmp_test_output/integrated_platform_runtime")
tmp_dir.mkdir(parents=True, exist_ok=True)

terrain_path = tmp_dir / "runtime_surface.asc"
terrain_path.write_text(
    "\n".join(
        [
            "ncols 4",
            "nrows 4",
            "xllcorner 0",
            "yllcorner 0",
            "cellsize 10",
            "NODATA_value -9999",
            "33 32 31 30",
            "32 31 30 29",
            "31 30 29 28",
            "30 29 28 27",
        ]
    ),
    encoding="utf-8",
)

geojson_path = tmp_dir / "runtime_site.geojson"
geojson_path.write_text(
    json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "Runtime Wall", "parcel": "primary"},
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [34, 0], [34, 34], [0, 34], [0, 0]]]},
                },
                {
                    "type": "Feature",
                    "properties": {"name": "Runtime Access", "highway": "service"},
                    "geometry": {"type": "LineString", "coordinates": [[-4, 17], [17, 17], [38, 17]]},
                },
            ],
        }
    ),
    encoding="utf-8",
)

workspace = Workspace()
workspace.command_manager.execute(AddEntityCommand(workspace.entities, LineEntity(Vector2(0, 0), Vector2(20, 0))))
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Runtime BIM", metadata={"release": "2.1"}))
workspace.bim_manager.initialize("Runtime BIM", project_units="meters")
storey = workspace.bim_manager.create_spatial_element("Building Storey", "Runtime Level", elevation=0.0)
wall = workspace.bim_manager.create_building_object(
    "Runtime Wall",
    "Wall",
    [{"body_id": "body-runtime-wall", "source": "BodyManager"}],
    spatial_container_id=storey.id,
)
workspace.bim_manager.create_bim_relationship("Contains", storey.id, [wall.id])

CreateGISProjectCommand(workspace, "Runtime GIS").execute()
ImportGISFileCommand(workspace, geojson_path, "Runtime Wall").execute()
CreateTerrainProjectCommand(workspace, "Runtime Terrain").execute()
terrain_import = ImportTerrainFileCommand(workspace, terrain_path, "Runtime Terrain Surface")
terrain_import.execute()
surface = terrain_import.surface
CreateSiteEngineeringProjectCommand(workspace, "Runtime Site").execute()
AddSiteBoundaryCommand(workspace, "Runtime Limit", "Construction Limit", [[0, 0], [34, 0], [34, 34], [0, 34]]).execute()
AnalyzeSiteDrainageCommand(workspace, surface, "Runtime Drainage").execute()
CreateInfrastructureProjectCommand(workspace, "Runtime Infrastructure").execute()
AddRoadCommand(workspace, "Runtime Access", [[-4, 17], [17, 17], [38, 17]], hierarchy="Collector").execute()
AddParcelCommand(workspace, "Runtime Parcel", [[0, 0], [34, 0], [34, 34], [0, 34]], {"parcel": "runtime"}, {"owner": "Workspace"}, {"phase": "certification"}).execute()
AddUtilityNetworkCommand(workspace, "Water", "Runtime Water", nodes=[{"id": "W1", "point": [0, 0]}, {"id": "W2", "point": [34, 34]}], edges=[{"from": "W1", "to": "W2"}]).execute()
CreateAISiteIntelligenceProjectCommand(workspace, "Runtime Intelligence", settings={"maximum_buildable_slope": 6.0, "preferred_buildable_slope": 1.5}).execute()
RunBuildabilityAnalysisCommand(workspace, surface).execute()
RunEnvironmentalAnalysisCommand(workspace, surface).execute()
RunConstraintIntelligenceCommand(workspace, surface).execute()
RunSitePlanningCommand(workspace, surface).execute()
GenerateAISiteEngineeringReportsCommand(workspace).execute()

workspace.command_manager.execute(InitializeIntegratedDesignPlatformCommand(workspace, "Runtime Integrated Project", "Release 2.1 Batch F"))
workspace.command_manager.execute(InitializeWorkflowOrchestratorCommand(workspace))
workflow = CreateWorkflowSessionCommand(workspace, "Site to Building Coordination", "Runtime Workflow", {"objective": "certify platform"})
workspace.command_manager.execute(workflow)
workspace.command_manager.execute(ExecuteWorkflowSessionCommand(workspace, workflow.session.id))
workspace.command_manager.execute(InitializeDataExchangeManagerCommand(workspace))
exchange = CreateDataExchangeSessionCommand(workspace, "Runtime Exchange")
workspace.command_manager.execute(exchange)
workspace.command_manager.execute(SynchronizeDataExchangeCommand(workspace, exchange.session.id))
workspace.command_manager.execute(InitializeDesignCoordinationCommand(workspace))
clash_detection = RunDesignClashDetectionCommand(workspace)
workspace.command_manager.execute(clash_detection)
coordination = workspace.integrated_design_manager.design_coordination_manager
first_clash = next(iter(coordination.clash_registry.values()))
issue = CreateCoordinationIssueCommand(workspace, "Runtime coordination issue", first_clash.clash_type, first_clash.severity, "High", first_clash.linked_objects, [first_clash.id])
workspace.command_manager.execute(issue)
workspace.command_manager.execute(CreateDesignReviewSessionCommand(workspace, "Runtime Review", issue_ids=[issue.issue.id], clash_ids=[first_clash.id]))
approval = CreateDesignApprovalSessionCommand(workspace, "Runtime Approval", issue_ids=[issue.issue.id])
workspace.command_manager.execute(approval)
workspace.command_manager.execute(RecordDesignApprovalDecisionCommand(workspace, approval.session.id, "Approved", reviewer="Runtime Lead"))
workspace.command_manager.execute(InitializeAutomationAICoordinationCommand(workspace))
automation_session = CreateAutomationSessionCommand(workspace, "Runtime Automation Session", template="Site to Building Coordination", ai_objective="Certify automation readiness")
workspace.command_manager.execute(automation_session)
workspace.command_manager.execute(ExecuteAutomationSessionCommand(workspace, automation_session.session.id))
workspace.command_manager.execute(CoordinateAITaskCommand(workspace, "Record runtime readiness", metadata={"release": "2.1", "batch": "F"}))

bootstrap = BootstrapIntegratedPlatformRuntimeCommand(workspace)
workspace.command_manager.execute(bootstrap)
runtime = workspace.integrated_design_manager.integrated_platform_runtime
assert bootstrap.state["status"] == "Bootstrapped"
assert bootstrap.state["geometry_owned_by_runtime"] is False
assert runtime.service_registry["Integrated Design Manager"]["available"] is True

startup = StartupIntegratedPlatformRuntimeCommand(workspace)
workspace.command_manager.execute(startup)
assert startup.state["lifecycle"] == "Running"
assert runtime.health_metadata["manager_registration"] is True
assert runtime.performance_metadata["command_execution_integrity"] is True

validation = ValidateIntegratedPlatformRuntimeCommand(workspace)
workspace.command_manager.execute(validation)
assert validation.report["valid"] is True, validation.report
assert validation.report["statistics"]["persistence"]["passed"] is True

certification = CertifyIntegratedPlatformRuntimeCommand(workspace)
workspace.command_manager.execute(certification)
assert certification.certification["status"] == "Certified", certification.certification
assert certification.certification["runtime_integrity_validation"] is True
assert certification.certification["compatibility_certification"]["release_2_1_batch_e"] is True
assert runtime.runtime_reports

visual = GenerateIntegratedPlatformRuntimeVisualizationCommand(workspace)
workspace.command_manager.execute(visual)
for key in ("runtime_health_overlays", "certification_overlays", "diagnostics_overlays", "status_overlays", "initialization_overlays", "validation_overlays"):
    assert key in visual.metadata

regression = RunIntegratedDesignRegressionCommand(workspace)
workspace.command_manager.execute(regression)
assert regression.result["passed"] is True
assert {item["name"] for item in regression.result["checks"]} >= {
    "Integrated Platform Runtime",
    "Runtime Lifecycle",
    "Runtime Bootstrap",
    "Runtime Health Monitoring",
    "Runtime Validation",
    "Production Certification",
    "Runtime Diagnostics",
}

shutdown = ShutdownIntegratedPlatformRuntimeCommand(workspace)
workspace.command_manager.execute(shutdown)
assert shutdown.state["lifecycle"] == "Stopped"

undo_count = workspace.command_manager.undo_count
workspace.command_manager.undo()
assert workspace.command_manager.undo_count == undo_count - 1
workspace.command_manager.redo()
assert workspace.command_manager.undo_count == undo_count

serializer = ProjectSerializer()
project_path = tmp_dir / "integrated_platform_runtime_project.json"
serializer.save(workspace, project_path)
restored = serializer.load(project_path)
restored_runtime = restored.integrated_design_manager.integrated_platform_runtime
assert restored_runtime.service_registry
assert restored_runtime.certification_records
assert restored_runtime.runtime_reports
assert restored_runtime.runtime_state["geometry_owned_by_runtime"] is False

print("production-integrated-platform-runtime-ok")

import json
from pathlib import Path

from engine.commands import (
    AddEntityCommand,
    AddParcelCommand,
    AddRoadCommand,
    AddSiteBoundaryCommand,
    AddUtilityNetworkCommand,
    AnalyzeSiteDrainageCommand,
    CreateAISiteIntelligenceProjectCommand,
    CreateBIMProjectCommand,
    CreateGISProjectCommand,
    CreateInfrastructureProjectCommand,
    CreateSiteEngineeringProjectCommand,
    CreateTerrainProjectCommand,
    CreateWorkflowSessionCommand,
    ExecuteWorkflowSessionCommand,
    GenerateAISiteEngineeringReportsCommand,
    GenerateWorkflowVisualizationCommand,
    ImportGISFileCommand,
    ImportTerrainFileCommand,
    InitializeIntegratedDesignPlatformCommand,
    InitializeWorkflowOrchestratorCommand,
    RunBuildabilityAnalysisCommand,
    RunConstraintIntelligenceCommand,
    RunEnvironmentalAnalysisCommand,
    RunIntegratedDesignRegressionCommand,
    RunSitePlanningCommand,
    ValidateWorkflowSessionCommand,
)
from engine.entities import LineEntity
from engine.geometry import Vector2
from engine.storage.project import ProjectSerializer
from engine.workspace.workspace import Workspace


tmp_dir = Path(".tmp_test_output/workflow_orchestration")
tmp_dir.mkdir(parents=True, exist_ok=True)

terrain_path = tmp_dir / "workflow_surface.asc"
terrain_path.write_text(
    "\n".join(
        [
            "ncols 4",
            "nrows 4",
            "xllcorner 0",
            "yllcorner 0",
            "cellsize 10",
            "NODATA_value -9999",
            "24 23 22 21",
            "23 22 21 20",
            "22 21 20 19",
            "21 20 19 18",
        ]
    ),
    encoding="utf-8",
)

geojson_path = tmp_dir / "workflow_site.geojson"
geojson_path.write_text(
    json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "Workflow Parcel", "parcel": "primary"},
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [30, 0], [30, 30], [0, 30], [0, 0]]]},
                },
                {
                    "type": "Feature",
                    "properties": {"name": "Workflow Road", "highway": "service"},
                    "geometry": {"type": "LineString", "coordinates": [[-5, 15], [20, 15], [40, 15]]},
                },
            ],
        }
    ),
    encoding="utf-8",
)

workspace = Workspace()
workspace.command_manager.execute(AddEntityCommand(workspace.entities, LineEntity(Vector2(0, 0), Vector2(12, 0))))
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Workflow BIM", metadata={"release": "2.1"}))
workspace.bim_manager.initialize("Workflow BIM", project_units="meters")
storey = workspace.bim_manager.create_spatial_element("Building Storey", "Workflow Level", elevation=0.0)
wall = workspace.bim_manager.create_building_object(
    "Workflow Wall",
    "Wall",
    [{"body_id": "body-workflow-wall", "source": "BodyManager"}],
    spatial_container_id=storey.id,
)
workspace.bim_manager.create_bim_relationship("Contains", storey.id, [wall.id])

CreateGISProjectCommand(workspace, "Workflow GIS").execute()
ImportGISFileCommand(workspace, geojson_path, "Workflow GIS Layer").execute()
CreateTerrainProjectCommand(workspace, "Workflow Terrain").execute()
terrain_import = ImportTerrainFileCommand(workspace, terrain_path, "Workflow Terrain Surface")
terrain_import.execute()
surface = terrain_import.surface
CreateSiteEngineeringProjectCommand(workspace, "Workflow Site").execute()
AddSiteBoundaryCommand(workspace, "Workflow Limit", "Construction Limit", [[0, 0], [30, 0], [30, 30], [0, 30]]).execute()
AnalyzeSiteDrainageCommand(workspace, surface, "Workflow Drainage").execute()
CreateInfrastructureProjectCommand(workspace, "Workflow Infrastructure").execute()
AddRoadCommand(workspace, "Workflow Access", [[-5, 15], [20, 15], [40, 15]], hierarchy="Collector").execute()
AddParcelCommand(workspace, "Workflow Parcel", [[0, 0], [30, 0], [30, 30], [0, 30]], {"parcel": "workflow"}, {"owner": "Workspace"}, {"phase": "orchestration"}).execute()
AddUtilityNetworkCommand(workspace, "Water", "Workflow Water", nodes=[{"id": "W1", "point": [0, 0]}, {"id": "W2", "point": [30, 30]}], edges=[{"from": "W1", "to": "W2"}]).execute()
CreateAISiteIntelligenceProjectCommand(workspace, "Workflow Intelligence", settings={"maximum_buildable_slope": 6.0, "preferred_buildable_slope": 1.5}).execute()
RunBuildabilityAnalysisCommand(workspace, surface).execute()
RunEnvironmentalAnalysisCommand(workspace, surface).execute()
RunConstraintIntelligenceCommand(workspace, surface).execute()
RunSitePlanningCommand(workspace, surface).execute()
GenerateAISiteEngineeringReportsCommand(workspace).execute()

workspace.command_manager.execute(InitializeIntegratedDesignPlatformCommand(workspace, "Workflow Integrated Project", "Release 2.1 Batch B"))
orchestrator_init = InitializeWorkflowOrchestratorCommand(workspace)
workspace.command_manager.execute(orchestrator_init)
orchestrator = workspace.integrated_design_manager.workflow_orchestrator
assert orchestrator.workflow_registry["BIM"]["implemented"] is True
assert orchestrator.workflow_registry["GIS"]["implemented"] is True
assert orchestrator.workflow_registry["Terrain"]["implemented"] is True
assert orchestrator.workflow_registry["Digital Twins"]["coordination_metadata"] is True
assert len(orchestrator.templates) >= 2

create_session = CreateWorkflowSessionCommand(workspace, "Site to Building Coordination", "Site Workflow Session", {"objective": "coordinate site and building readiness"})
workspace.command_manager.execute(create_session)
session = create_session.session
assert session.status == "Ready"
assert session.command_sequence
assert session.execution_order == ["gis-context", "terrain-context", "site-review", "infrastructure-review", "bim-coordination", "ai-site-review"]
assert session.validation_report["valid"] is True

validate = ValidateWorkflowSessionCommand(workspace, session.id)
workspace.command_manager.execute(validate)
assert validate.report["valid"] is True
assert validate.report["statistics"]["persistence"]["passed"] is True

execute = ExecuteWorkflowSessionCommand(workspace, session.id)
workspace.command_manager.execute(execute)
assert execute.result.status == "Completed"
assert execute.result.replay_metadata["uses_existing_command_system"] is True
assert execute.result.replay_metadata["geometry_owned_by_workflow"] is False
assert len(execute.result.checkpoints) >= 2
assert orchestrator.workflow_graph["edges"]
assert orchestrator.execution_graph["edges"]
assert orchestrator.reference_graph["edges"]
assert orchestrator.notifications

visual = GenerateWorkflowVisualizationCommand(workspace)
workspace.command_manager.execute(visual)
for key in ("workflow_overlays", "dependency_overlays", "execution_status_overlays", "notification_overlays", "validation_overlays", "diagnostics"):
    assert key in visual.metadata

regression = RunIntegratedDesignRegressionCommand(workspace)
workspace.command_manager.execute(regression)
assert regression.result["passed"] is True
assert {item["name"] for item in regression.result["checks"]} >= {
    "Workflow Orchestrator",
    "Workflow Registry",
    "Workflow Execution",
    "Workflow Persistence",
    "Workflow Diagnostics",
}

undo_count = workspace.command_manager.undo_count
workspace.command_manager.undo()
assert workspace.command_manager.undo_count == undo_count - 1
workspace.command_manager.redo()
assert workspace.command_manager.undo_count == undo_count

serializer = ProjectSerializer()
project_path = tmp_dir / "workflow_project.json"
serializer.save(workspace, project_path)
restored = serializer.load(project_path)
restored_orchestrator = restored.integrated_design_manager.workflow_orchestrator
assert restored_orchestrator.sessions[-1].status == "Completed"
assert restored_orchestrator.workflow_registry["BIM"]["implemented"] is True
assert restored_orchestrator.workflow_graph["edges"]
assert restored.integrated_design_manager.context.name == "Workflow Integrated Project"

print("cross-discipline-workflow-orchestration-ok")

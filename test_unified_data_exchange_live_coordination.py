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
    CreateDataExchangeSessionCommand,
    CreateGISProjectCommand,
    CreateInfrastructureProjectCommand,
    CreateSiteEngineeringProjectCommand,
    CreateTerrainProjectCommand,
    CreateWorkflowSessionCommand,
    ExecuteWorkflowSessionCommand,
    GenerateAISiteEngineeringReportsCommand,
    GenerateDataExchangeVisualizationCommand,
    ImportGISFileCommand,
    ImportTerrainFileCommand,
    InitializeDataExchangeManagerCommand,
    InitializeIntegratedDesignPlatformCommand,
    InitializeWorkflowOrchestratorCommand,
    QueryDataExchangeCommand,
    RunBuildabilityAnalysisCommand,
    RunConstraintIntelligenceCommand,
    RunEnvironmentalAnalysisCommand,
    RunIntegratedDesignRegressionCommand,
    RunSitePlanningCommand,
    SynchronizeDataExchangeCommand,
    ValidateDataExchangeCommand,
)
from engine.entities import LineEntity
from engine.geometry import Vector2
from engine.storage.project import ProjectSerializer
from engine.workspace.workspace import Workspace


tmp_dir = Path(".tmp_test_output/data_exchange")
tmp_dir.mkdir(parents=True, exist_ok=True)

terrain_path = tmp_dir / "exchange_surface.asc"
terrain_path.write_text(
    "\n".join(
        [
            "ncols 4",
            "nrows 4",
            "xllcorner 0",
            "yllcorner 0",
            "cellsize 10",
            "NODATA_value -9999",
            "27 26 25 24",
            "26 25 24 23",
            "25 24 23 22",
            "24 23 22 21",
        ]
    ),
    encoding="utf-8",
)

geojson_path = tmp_dir / "exchange_site.geojson"
geojson_path.write_text(
    json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "Exchange Parcel", "parcel": "primary"},
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [30, 0], [30, 30], [0, 30], [0, 0]]]},
                },
                {
                    "type": "Feature",
                    "properties": {"name": "Exchange Road", "highway": "service"},
                    "geometry": {"type": "LineString", "coordinates": [[-5, 15], [20, 15], [40, 15]]},
                },
            ],
        }
    ),
    encoding="utf-8",
)

workspace = Workspace()
workspace.command_manager.execute(AddEntityCommand(workspace.entities, LineEntity(Vector2(0, 0), Vector2(14, 0))))
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Exchange BIM", metadata={"release": "2.1"}))
workspace.bim_manager.initialize("Exchange BIM", project_units="meters")
storey = workspace.bim_manager.create_spatial_element("Building Storey", "Exchange Level", elevation=0.0)
wall = workspace.bim_manager.create_building_object(
    "Exchange Wall",
    "Wall",
    [{"body_id": "body-exchange-wall", "source": "BodyManager"}],
    spatial_container_id=storey.id,
)
workspace.bim_manager.create_bim_relationship("Contains", storey.id, [wall.id])

CreateGISProjectCommand(workspace, "Exchange GIS").execute()
ImportGISFileCommand(workspace, geojson_path, "Exchange GIS Layer").execute()
CreateTerrainProjectCommand(workspace, "Exchange Terrain").execute()
terrain_import = ImportTerrainFileCommand(workspace, terrain_path, "Exchange Terrain Surface")
terrain_import.execute()
surface = terrain_import.surface
CreateSiteEngineeringProjectCommand(workspace, "Exchange Site").execute()
AddSiteBoundaryCommand(workspace, "Exchange Limit", "Construction Limit", [[0, 0], [30, 0], [30, 30], [0, 30]]).execute()
AnalyzeSiteDrainageCommand(workspace, surface, "Exchange Drainage").execute()
CreateInfrastructureProjectCommand(workspace, "Exchange Infrastructure").execute()
AddRoadCommand(workspace, "Exchange Access", [[-5, 15], [20, 15], [40, 15]], hierarchy="Collector").execute()
AddParcelCommand(workspace, "Exchange Parcel", [[0, 0], [30, 0], [30, 30], [0, 30]], {"parcel": "exchange"}, {"owner": "Workspace"}, {"phase": "coordination"}).execute()
AddUtilityNetworkCommand(workspace, "Water", "Exchange Water", nodes=[{"id": "W1", "point": [0, 0]}, {"id": "W2", "point": [30, 30]}], edges=[{"from": "W1", "to": "W2"}]).execute()
CreateAISiteIntelligenceProjectCommand(workspace, "Exchange Intelligence", settings={"maximum_buildable_slope": 6.0, "preferred_buildable_slope": 1.5}).execute()
RunBuildabilityAnalysisCommand(workspace, surface).execute()
RunEnvironmentalAnalysisCommand(workspace, surface).execute()
RunConstraintIntelligenceCommand(workspace, surface).execute()
RunSitePlanningCommand(workspace, surface).execute()
GenerateAISiteEngineeringReportsCommand(workspace).execute()

workspace.command_manager.execute(InitializeIntegratedDesignPlatformCommand(workspace, "Data Exchange Integrated Project", "Release 2.1 Batch C"))
workspace.command_manager.execute(InitializeWorkflowOrchestratorCommand(workspace))
workflow = CreateWorkflowSessionCommand(workspace, "Site to Building Coordination", "Exchange Workflow", {"objective": "coordinate live data"})
workspace.command_manager.execute(workflow)
workspace.command_manager.execute(ExecuteWorkflowSessionCommand(workspace, workflow.session.id))

initialize_exchange = InitializeDataExchangeManagerCommand(workspace)
workspace.command_manager.execute(initialize_exchange)
exchange = workspace.integrated_design_manager.data_exchange_manager
assert exchange.shared_data_registry
assert exchange.live_coordination_context["single_project_model"] is True
assert exchange.synchronization_state["status"] == "Synchronized"

create_exchange = CreateDataExchangeSessionCommand(workspace, "Live Exchange Session")
workspace.command_manager.execute(create_exchange)
session = create_exchange.session
assert session.status == "Ready"
assert session.shared_references
assert session.validation_report["valid"] is True

synchronize = SynchronizeDataExchangeCommand(workspace, session.id)
workspace.command_manager.execute(synchronize)
assert synchronize.state["status"] == "Synchronized"
assert synchronize.state["reference_updates"] >= len(session.shared_references)
assert exchange.notifications

query = QueryDataExchangeCommand(workspace, "BIM", "Wall")
workspace.command_manager.execute(query)
assert any("Wall" in item["name"] for item in query.results)

validation = ValidateDataExchangeCommand(workspace, session.id)
workspace.command_manager.execute(validation)
assert validation.report["valid"] is True
assert validation.report["statistics"]["persistence"]["passed"] is True
assert validation.report["statistics"]["registry_items"] == len(exchange.shared_data_registry)

visual = GenerateDataExchangeVisualizationCommand(workspace)
workspace.command_manager.execute(visual)
for key in ("synchronization_overlays", "reference_overlays", "relationship_overlays", "coordination_status_overlays", "notification_overlays", "validation_overlays", "diagnostics"):
    assert key in visual.metadata

regression = RunIntegratedDesignRegressionCommand(workspace)
workspace.command_manager.execute(regression)
assert regression.result["passed"] is True
assert {item["name"] for item in regression.result["checks"]} >= {
    "Data Exchange Manager",
    "Shared Data Registry",
    "Live Coordination",
    "Synchronization",
    "Unified Data Model",
    "Reference Validation",
    "Data Exchange Persistence",
    "Data Exchange Diagnostics",
}

undo_count = workspace.command_manager.undo_count
workspace.command_manager.undo()
assert workspace.command_manager.undo_count == undo_count - 1
workspace.command_manager.redo()
assert workspace.command_manager.undo_count == undo_count

serializer = ProjectSerializer()
project_path = tmp_dir / "data_exchange_project.json"
serializer.save(workspace, project_path)
restored = serializer.load(project_path)
restored_exchange = restored.integrated_design_manager.data_exchange_manager
assert restored_exchange.exchange_sessions[-1].status in {"Ready", "Synchronized"}
assert restored_exchange.shared_data_registry
assert restored_exchange.live_coordination_context["single_project_model"] is True
assert restored.integrated_design_manager.workflow_orchestrator.sessions

print("unified-data-exchange-live-coordination-ok")

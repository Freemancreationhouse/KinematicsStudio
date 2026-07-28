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
    GenerateAISiteEngineeringReportsCommand,
    GenerateIntegratedVisualizationCommand,
    ImportGISFileCommand,
    ImportTerrainFileCommand,
    InitializeIntegratedDesignPlatformCommand,
    MapIntegratedDependenciesCommand,
    RefreshIntegratedProjectIndexCommand,
    RegisterUnifiedCommandsCommand,
    RunBuildabilityAnalysisCommand,
    RunConstraintIntelligenceCommand,
    RunEnvironmentalAnalysisCommand,
    RunIntegratedDesignRegressionCommand,
    RunSitePlanningCommand,
    ValidateIntegratedDesignPlatformCommand,
)
from engine.entities import LineEntity
from engine.geometry import Vector2
from engine.storage.project import ProjectSerializer
from engine.workspace.workspace import Workspace


tmp_dir = Path(".tmp_test_output/integrated_design")
tmp_dir.mkdir(parents=True, exist_ok=True)

terrain_path = tmp_dir / "integrated_surface.asc"
terrain_path.write_text(
    "\n".join(
        [
            "ncols 4",
            "nrows 4",
            "xllcorner 0",
            "yllcorner 0",
            "cellsize 10",
            "NODATA_value -9999",
            "21 20 19 18",
            "20 19 18 17",
            "19 18 17 16",
            "18 17 16 15",
        ]
    ),
    encoding="utf-8",
)

geojson_path = tmp_dir / "integrated_site.geojson"
geojson_path.write_text(
    json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "Integrated Parcel", "parcel": "primary"},
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [30, 0], [30, 30], [0, 30], [0, 0]]]},
                },
                {
                    "type": "Feature",
                    "properties": {"name": "Integrated Road", "highway": "service"},
                    "geometry": {"type": "LineString", "coordinates": [[-5, 15], [20, 15], [40, 15]]},
                },
            ],
        }
    ),
    encoding="utf-8",
)

workspace = Workspace()
workspace.command_manager.execute(AddEntityCommand(workspace.entities, LineEntity(Vector2(0, 0), Vector2(10, 0))))
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Integrated BIM", metadata={"release": "2.1"}))
workspace.bim_manager.initialize("Integrated BIM", project_units="meters")
storey = workspace.bim_manager.create_spatial_element("Building Storey", "Level 01", elevation=0.0)
wall = workspace.bim_manager.create_building_object(
    "Integrated Wall",
    "Wall",
    [{"body_id": "body-integrated-wall", "source": "BodyManager"}],
    spatial_container_id=storey.id,
)
workspace.bim_manager.create_bim_relationship("Contains", storey.id, [wall.id])

CreateGISProjectCommand(workspace, "Integrated GIS").execute()
ImportGISFileCommand(workspace, geojson_path, "Integrated GIS Layer").execute()
CreateTerrainProjectCommand(workspace, "Integrated Terrain").execute()
terrain_import = ImportTerrainFileCommand(workspace, terrain_path, "Integrated Terrain Surface")
terrain_import.execute()
surface = terrain_import.surface
CreateSiteEngineeringProjectCommand(workspace, "Integrated Site").execute()
AddSiteBoundaryCommand(workspace, "Integrated Limit", "Construction Limit", [[0, 0], [30, 0], [30, 30], [0, 30]]).execute()
AnalyzeSiteDrainageCommand(workspace, surface, "Integrated Drainage").execute()
CreateInfrastructureProjectCommand(workspace, "Integrated Infrastructure").execute()
AddRoadCommand(workspace, "Integrated Access", [[-5, 15], [20, 15], [40, 15]], hierarchy="Collector").execute()
AddParcelCommand(workspace, "Integrated Parcel", [[0, 0], [30, 0], [30, 30], [0, 30]], {"parcel": "integrated"}, {"owner": "Workspace"}, {"phase": "foundation"}).execute()
AddUtilityNetworkCommand(workspace, "Water", "Integrated Water", nodes=[{"id": "W1", "point": [0, 0]}, {"id": "W2", "point": [30, 30]}], edges=[{"from": "W1", "to": "W2"}]).execute()
CreateAISiteIntelligenceProjectCommand(workspace, "Integrated Intelligence", settings={"maximum_buildable_slope": 6.0, "preferred_buildable_slope": 1.5}).execute()
RunBuildabilityAnalysisCommand(workspace, surface).execute()
RunEnvironmentalAnalysisCommand(workspace, surface).execute()
RunConstraintIntelligenceCommand(workspace, surface).execute()
RunSitePlanningCommand(workspace, surface).execute()
GenerateAISiteEngineeringReportsCommand(workspace).execute()

manager = workspace.integrated_design_manager
initialize = InitializeIntegratedDesignPlatformCommand(workspace, "Integrated Design Validation", "Release 2.1 Batch A")
workspace.command_manager.execute(initialize)
assert initialize.context.active is True
assert manager.discipline_registry["bim"]["available"] is True
assert manager.discipline_registry["gis"]["available"] is True
assert manager.discipline_registry["terrain"]["available"] is True
assert manager.discipline_registry["infrastructure"]["available"] is True

refresh = RefreshIntegratedProjectIndexCommand(workspace)
workspace.command_manager.execute(refresh)
assert any(item["discipline"] == "BIM" for item in refresh.index.values())
assert any(item["discipline"] == "GIS" for item in refresh.index.values())
assert any(item["discipline"] == "Terrain" for item in refresh.index.values())
assert any(item["discipline"] == "Infrastructure" for item in refresh.index.values())

mapping = MapIntegratedDependenciesCommand(workspace)
workspace.command_manager.execute(mapping)
assert mapping.graph["single_workspace"] is True
assert mapping.graph["edges"]

commands = RegisterUnifiedCommandsCommand(workspace)
workspace.command_manager.execute(commands)
assert commands.catalog["single_history"] is True
assert all(commands.catalog["families"].values())

validation = ValidateIntegratedDesignPlatformCommand(workspace)
workspace.command_manager.execute(validation)
assert validation.report["valid"] is True
assert not validation.report["issues"]
assert validation.report["statistics"]["persistence"]["passed"] is True

regression = RunIntegratedDesignRegressionCommand(workspace)
workspace.command_manager.execute(regression)
assert regression.result["passed"] is True
assert {item["name"] for item in regression.result["checks"]} >= {
    "Release 1.9 complete",
    "Release 2.0 complete",
    "Workspace",
    "Command System",
    "Persistence",
    "Undo/Redo",
    "History",
    "Renderer",
    "Shared Project Indexing",
    "Cross-Discipline Coordination",
}

visual = GenerateIntegratedVisualizationCommand(workspace)
workspace.command_manager.execute(visual)
for key in ("discipline_overlays", "relationship_overlays", "dependency_overlays", "selection_overlays", "validation_overlays", "diagnostics"):
    assert key in visual.metadata

undo_count = workspace.command_manager.undo_count
workspace.command_manager.undo()
assert workspace.command_manager.undo_count == undo_count - 1
workspace.command_manager.redo()
assert workspace.command_manager.undo_count == undo_count

serializer = ProjectSerializer()
project_path = tmp_dir / "integrated_design_project.json"
serializer.save(workspace, project_path)
restored = serializer.load(project_path)
restored_manager = restored.integrated_design_manager
assert restored_manager.context.name == "Integrated Design Validation"
assert restored_manager.diagnostics.status in {"Operational", "Blocked"}
assert restored_manager.shared_engineering_context["single_workspace"] is True
assert restored_manager.discipline_registry["bim"]["available"] is True
assert restored_manager.discipline_registry["terrain"]["available"] is True

print("integrated-design-platform-foundation-ok")

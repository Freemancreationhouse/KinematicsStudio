import json
from pathlib import Path

from engine.commands import (
    AddParcelCommand,
    AddRoadCommand,
    AddSiteBoundaryCommand,
    AddUtilityNetworkCommand,
    AnalyzeSiteDrainageCommand,
    CertifyTerrainCompatibilityCommand,
    CertifyTerrainReleaseCommand,
    CleanupTerrainRuntimeCommand,
    CreateAISiteIntelligenceProjectCommand,
    CreateGISProjectCommand,
    CreateInfrastructureProjectCommand,
    CreateSiteEngineeringProjectCommand,
    CreateTerrainProjectCommand,
    GenerateAISiteEngineeringReportsCommand,
    GenerateTerrainRuntimeVisualizationCommand,
    ImportGISFileCommand,
    ImportTerrainFileCommand,
    InitializeTerrainProductionRuntimeCommand,
    OptimizeTerrainRuntimeCommand,
    RunBuildabilityAnalysisCommand,
    RunConstraintIntelligenceCommand,
    RunEnvironmentalAnalysisCommand,
    RunSitePlanningCommand,
    RunTerrainProductionRegressionCommand,
    ValidateTerrainRuntimeCommand,
)
from engine.storage.project import ProjectSerializer
from engine.workspace.workspace import Workspace


tmp_dir = Path(".tmp_test_output/terrain_runtime")
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
            "18 17 16 15",
            "17 16 15 14",
            "16 15 14 13",
            "15 14 13 12",
        ]
    ),
    encoding="utf-8",
)
geojson_path = tmp_dir / "runtime_gis.geojson"
geojson_path.write_text(
    json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {"name": "Runtime Parcel", "parcel": "lot"}, "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [30, 0], [30, 30], [0, 30], [0, 0]]]}},
                {"type": "Feature", "properties": {"name": "Runtime Road", "highway": "service"}, "geometry": {"type": "LineString", "coordinates": [[-5, 15], [20, 15], [40, 15]]}},
            ],
        }
    ),
    encoding="utf-8",
)

workspace = Workspace()
CreateGISProjectCommand(workspace, "Runtime GIS").execute()
ImportGISFileCommand(workspace, geojson_path, "Runtime GIS Layer").execute()
CreateTerrainProjectCommand(workspace, "Runtime Terrain").execute()
terrain_import = ImportTerrainFileCommand(workspace, terrain_path, "Runtime Surface")
terrain_import.execute()
surface = terrain_import.surface
CreateSiteEngineeringProjectCommand(workspace, "Runtime Site").execute()
AddSiteBoundaryCommand(workspace, "Runtime Limit", "Construction Limit", [[0, 0], [30, 0], [30, 30], [0, 30]]).execute()
AnalyzeSiteDrainageCommand(workspace, surface, "Runtime Drainage").execute()
CreateInfrastructureProjectCommand(workspace, "Runtime Infrastructure").execute()
AddRoadCommand(workspace, "Runtime Access", [[-5, 15], [20, 15], [40, 15]], hierarchy="Collector").execute()
AddParcelCommand(workspace, "Runtime Development Parcel", [[0, 0], [30, 0], [30, 30], [0, 30]], {"parcel": "runtime"}, {"owner": "Runtime"}, {"phase": "certification"}).execute()
AddUtilityNetworkCommand(workspace, "Water", "Runtime Water", nodes=[{"id": "W1", "point": [0, 0]}, {"id": "W2", "point": [30, 30]}], edges=[{"from": "W1", "to": "W2"}]).execute()
CreateAISiteIntelligenceProjectCommand(workspace, "Runtime Intelligence", settings={"maximum_buildable_slope": 5.0, "preferred_buildable_slope": 1.0}).execute()
RunBuildabilityAnalysisCommand(workspace, surface).execute()
RunEnvironmentalAnalysisCommand(workspace, surface).execute()
RunConstraintIntelligenceCommand(workspace, surface).execute()
RunSitePlanningCommand(workspace, surface).execute()
GenerateAISiteEngineeringReportsCommand(workspace).execute()

runtime = workspace.gis_manager.terrain_production_runtime
init = InitializeTerrainProductionRuntimeCommand(workspace, configuration={"performance_thresholds": {"max_validation_issues": 0, "min_health_score": 70.0}})
init.execute()
assert init.session.status == "Completed"
init.undo()
assert not runtime.sessions
init.execute()

optimization = OptimizeTerrainRuntimeCommand(workspace)
optimization.execute()
assert optimization.report["metadata_index"]["terrain_surfaces"]
assert optimization.report["spatial_indexing"]["terrain_surface_entries"] == 1
assert optimization.report["performance_diagnostics"]["performance_score"] >= 70.0

validation = ValidateTerrainRuntimeCommand(workspace)
validation.execute()
assert validation.report["valid"] is True
assert not validation.report["issues"]
assert validation.report["statistics"]["persistence_validation"]["passed"] is True

regression = RunTerrainProductionRegressionCommand(workspace)
regression.execute()
assert regression.result["passed"] is True
assert {check["name"] for check in regression.result["checks"]} >= {"GIS Foundation", "Terrain Modeling", "Site Engineering", "Infrastructure", "AI Site Intelligence", "Persistence", "Undo/Redo", "History", "Renderer", "Import/Export"}

compatibility = CertifyTerrainCompatibilityCommand(workspace)
compatibility.execute()
assert compatibility.report["compatible"] is True
assert all(item["compatible"] for item in compatibility.report["release_matrix"].values())

cleanup = CleanupTerrainRuntimeCommand(workspace)
cleanup.execute()
assert cleanup.event["event"] == "Resource cleanup"

certification = CertifyTerrainReleaseCommand(workspace)
certification.execute()
assert certification.record["status"] == "Certified"
assert certification.record["production_ready"] is True
assert certification.record["architecture_compliance"]["body_manager_geometry_owner"] is True
assert workspace.gis_manager.ensure_project().metadata["release_2_0_status"] == "COMPLETE"

visual = GenerateTerrainRuntimeVisualizationCommand(workspace)
visual.execute()
for key in ("performance_overlays", "validation_overlays", "diagnostics_overlays", "health_indicators", "certification_summaries"):
    assert key in visual.metadata

serializer = ProjectSerializer()
project_path = tmp_dir / "terrain_runtime_project.json"
serializer.save(workspace, project_path)
restored = serializer.load(project_path)
restored_runtime = restored.gis_manager.terrain_production_runtime
assert restored_runtime.certification_records[-1]["status"] == "Certified"
assert restored_runtime.regression_results[-1]["passed"] is True
assert restored.gis_manager.ensure_project().metadata["release_2_0_status"] == "COMPLETE"

print("terrain-production-runtime-ok")

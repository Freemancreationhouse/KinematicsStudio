from pathlib import Path

from engine.commands import (
    AddParcelCommand,
    AddRoadCommand,
    AddSiteBoundaryCommand,
    AddUtilityNetworkCommand,
    AnalyzeSiteDrainageCommand,
    CreateAISiteIntelligenceProjectCommand,
    CreateGISProjectCommand,
    CreateInfrastructureProjectCommand,
    CreateSiteEngineeringProjectCommand,
    CreateTerrainProjectCommand,
    GenerateAISiteEngineeringReportsCommand,
    ImportTerrainFileCommand,
    RunBuildabilityAnalysisCommand,
    RunConstraintIntelligenceCommand,
    RunEnvironmentalAnalysisCommand,
    RunSitePlanningCommand,
    ValidateAISiteIntelligenceCommand,
)
from engine.storage.project import ProjectSerializer
from engine.workspace.workspace import Workspace


tmp_dir = Path(".tmp_test_output/ai_site_intelligence")
tmp_dir.mkdir(parents=True, exist_ok=True)
grid_path = tmp_dir / "intelligence_surface.asc"
grid_path.write_text(
    "\n".join(
        [
            "ncols 5",
            "nrows 5",
            "xllcorner 0",
            "yllcorner 0",
            "cellsize 10",
            "NODATA_value -9999",
            "24 22 20 18 16",
            "22 20 18 16 14",
            "20 18 15 13 12",
            "18 16 13 11 10",
            "16 14 12 10 8",
        ]
    ),
    encoding="utf-8",
)

workspace = Workspace()
CreateGISProjectCommand(workspace, "GIS").execute()
CreateTerrainProjectCommand(workspace, "Terrain").execute()
CreateSiteEngineeringProjectCommand(workspace, "Site").execute()
CreateInfrastructureProjectCommand(workspace, "Infrastructure").execute()
CreateAISiteIntelligenceProjectCommand(
    workspace,
    "Site Intelligence",
    settings={
        "maximum_buildable_slope": 0.001,
        "preferred_buildable_slope": 0.5,
        "minimum_road_access_distance": 45.0,
        "minimum_utility_clearance": 3.0,
        "setback_distance": 4.0,
        "north_azimuth": 0.0,
        "prevailing_wind_azimuth": 270.0,
        "rainfall_intensity": 40.0,
        "flood_accumulation_threshold": 4,
    },
).execute()

terrain = workspace.gis_manager.terrain_manager
site = terrain.site_engineering_manager
infra = site.infrastructure_manager
ai_site = infra.ai_site_intelligence_manager

terrain_import = ImportTerrainFileCommand(workspace, grid_path, name="AI Existing Terrain")
terrain_import.execute()
surface = terrain_import.surface

AddSiteBoundaryCommand(workspace, "Protected Creek", "Protected Area", [[0, 0], [12, 0], [12, 12], [0, 12]]).execute()
AddSiteBoundaryCommand(workspace, "Front Setback", "Setback", [[0, 0], [40, 0], [40, 5], [0, 5]]).execute()
AddRoadCommand(workspace, "Access Road", [[-10, 20], [20, 20], [50, 20]], hierarchy="Collector").execute()
AddParcelCommand(workspace, "Development Parcel", [[0, 0], [40, 0], [40, 40], [0, 40]], {"parcel": "development"}, {"owner": "Owner"}, {"phase": "1"}).execute()
AddUtilityNetworkCommand(
    workspace,
    "Water",
    "Water Main",
    nodes=[{"id": "W1", "point": [5, 5]}, {"id": "W2", "point": [30, 30]}],
    edges=[{"from": "W1", "to": "W2"}],
).execute()
AnalyzeSiteDrainageCommand(workspace, surface, "Drainage for Intelligence").execute()

build = RunBuildabilityAnalysisCommand(workspace, surface, "Deterministic Buildability")
build.execute()
assert 0.0 <= build.report["construction_feasibility"] <= 100.0
assert build.report["foundation_suitability_metadata"]["maximum_slope"] >= 0.0
assert build.report["accessibility_analysis"]["nearest_road_distance"] < 45.0
assert build.report["recommendations"]
build.undo()
assert not ai_site.ensure_project().buildability_reports
build.execute()

environment = RunEnvironmentalAnalysisCommand(workspace, surface, "Deterministic Environment")
environment.execute()
assert 0.0 <= environment.report["environmental_suitability"] <= 100.0
assert "solar_orientation" in environment.report
assert "flood_risk_metadata" in environment.report

constraints = RunConstraintIntelligenceCommand(workspace, surface, "Deterministic Constraints")
constraints.execute()
assert constraints.report["protected_zones"]
assert constraints.report["setbacks"]
assert constraints.report["slope_restrictions"]
assert constraints.report["utility_conflicts"]

planning = RunSitePlanningCommand(workspace, surface, "Deterministic Planning")
planning.execute()
assert planning.report["building_placement_suggestions"]
assert planning.report["road_access_suggestions"]
assert planning.report["parking_location_suggestions"]
assert planning.report["service_access_suggestions"]
assert planning.report["development_zones"]
assert planning.report["engineering_validation"]["valid"] is True

summary = GenerateAISiteEngineeringReportsCommand(workspace, "Engineering Intelligence Summary")
summary.execute()
assert summary.report["site_suitability_report"]
assert summary.report["environmental_report"]
assert summary.report["constraint_report"]
assert summary.report["engineering_recommendation_report"]
assert summary.report["summary_report"]["planning_candidates"] > 0

visual = ai_site.visualization_metadata()
for key in ("suitability_overlays", "constraint_overlays", "recommendation_overlays", "solar_overlays", "wind_overlays", "flood_overlays", "engineering_diagnostics"):
    assert key in visual

ValidateAISiteIntelligenceCommand(workspace).execute()
report = ai_site.ensure_project().validation_report
assert report.valid is True
assert not report.issues
assert ai_site.ensure_project().diagnostics.analyses >= 4
assert ai_site.ensure_project().diagnostics.recommendations >= 3
assert ai_site.ensure_project().diagnostics.constraints >= 4
assert ai_site.ensure_project().diagnostics.reports == 1

serializer = ProjectSerializer()
project_path = tmp_dir / "ai_site_intelligence_project.json"
serializer.save(workspace, project_path)
restored = serializer.load(project_path)
restored_ai = restored.gis_manager.terrain_manager.site_engineering_manager.infrastructure_manager.ai_site_intelligence_manager
assert restored_ai.ensure_project().buildability_reports
assert restored_ai.ensure_project().environmental_reports
assert restored_ai.ensure_project().planning_reports
assert restored_ai.ensure_project().constraint_reports
assert restored_ai.ensure_project().engineering_reports
assert restored_ai.ensure_project().validation_report.valid is True

print("ai-site-intelligence-ok")

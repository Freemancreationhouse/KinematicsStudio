from pathlib import Path

from engine.commands import (
    AddSiteBoundaryCommand,
    AnalyzeSiteDrainageCommand,
    AnalyzeSiteSlopeCommand,
    ApplySiteGradingCommand,
    ComputeCutFillCommand,
    CreateGISProjectCommand,
    CreateSiteEngineeringProjectCommand,
    CreateSiteProfileCommand,
    CreateSiteSectionCommand,
    CreateTerrainProjectCommand,
    ImportTerrainFileCommand,
    ValidateSiteEngineeringCommand,
)
from engine.storage.project import ProjectSerializer
from engine.workspace.workspace import Workspace


tmp_dir = Path(".tmp_test_output/site_engineering")
tmp_dir.mkdir(parents=True, exist_ok=True)
grid_path = tmp_dir / "civil_surface.asc"
grid_path.write_text(
    "\n".join(
        [
            "ncols 4",
            "nrows 4",
            "xllcorner 0",
            "yllcorner 0",
            "cellsize 10",
            "NODATA_value -9999",
            "16 15 14 13",
            "15 14 13 12",
            "14 13 12 11",
            "13 12 11 10",
        ]
    ),
    encoding="utf-8",
)

workspace = Workspace()
CreateGISProjectCommand(workspace, "GIS Site").execute()
CreateTerrainProjectCommand(workspace, "Terrain").execute()
site_project_command = CreateSiteEngineeringProjectCommand(workspace, "Civil Site")
site_project_command.execute()

terrain = workspace.gis_manager.terrain_manager
site = terrain.site_engineering_manager
import_command = ImportTerrainFileCommand(workspace, grid_path, name="Civil Existing")
import_command.execute()
surface = import_command.surface
original_first_elevation = surface.points[0][2]

boundary = AddSiteBoundaryCommand(workspace, "Property Boundary", "Property", [[0, 0], [30, 0], [30, 30], [0, 30]])
boundary.execute()
construction = AddSiteBoundaryCommand(workspace, "Construction Limit", "Construction Limit", [[5, 5], [25, 5], [25, 25], [5, 25]])
construction.execute()
assert boundary.record["area"] == 900.0
construction.undo()
assert len(site.ensure_project().boundaries) == 1
construction.execute()

pad = ApplySiteGradingCommand(workspace, surface, "pad", {"bounds": [0, 0, 30, 30]}, {"elevation": 13.0})
pad.execute()
assert surface.points[0][2] == 13.0
pad.undo()
assert surface.points[0][2] == original_first_elevation
pad.execute()

volume = ComputeCutFillCommand(workspace, surface, region={"bounds": [0, 0, 30, 30]}, name="Pad Earthwork")
volume.execute()
assert volume.report["fill_volume"] > 0.0
assert volume.report["cut_volume"] > 0.0
assert abs(volume.report["net_volume"] - (volume.report["fill_volume"] - volume.report["cut_volume"])) < 1e-9
volume.undo()
assert not site.ensure_project().volume_reports
volume.execute()

road = ApplySiteGradingCommand(
    workspace,
    surface,
    "road",
    {"bounds": [0, 0, 30, 30], "centerline": [[0, 0, 18.0], [30, 30, 20.0]]},
    {"start_elevation": 18.0, "end_elevation": 20.0, "cross_slope": 2.0},
)
road.execute()
slope_grade = ApplySiteGradingCommand(workspace, surface, "slope", {"bounds": [0, 0, 30, 30]}, {"start": [0, 0, 18.0], "end": [30, 30, 24.0]})
slope_grade.execute()
automatic = ApplySiteGradingCommand(workspace, surface, "automatic", {"bounds": [0, 0, 30, 30]}, {"constraints": [[0, 0, 16], [30, 30, 22], [0, 30, 19]]})
automatic.execute()
breakline = ApplySiteGradingCommand(workspace, surface, "grade breakline", {"bounds": [0, 0, 30, 30]}, {"breakline": [[0, 0, 18], [30, 30, 21]]})
breakline.execute()
assert len(site.ensure_project().grading_operations) >= 5

slope = AnalyzeSiteSlopeCommand(workspace, surface, classes=[0, 5, 10, 20, 33], name="Engineering Slope")
slope.execute()
assert slope.report["maximum_slope"] >= slope.report["minimum_slope"]
assert slope.report["triangles_evaluated"] == len(surface.triangles)
assert slope.report["color_classification_metadata"]

drainage = AnalyzeSiteDrainageCommand(workspace, surface, name="Drainage")
drainage.execute()
assert drainage.report["flow_direction"]
assert drainage.report["flow_accumulation"]
assert drainage.report["low_points"]
assert drainage.report["catchment_areas"]

section = CreateSiteSectionCommand(workspace, surface, "Section A", [[0, 0], [30, 0]], interval=10.0)
section.execute()
assert len(section.record["samples"]) == 4
section.undo()
assert not site.ensure_project().sections
section.execute()

profile = CreateSiteProfileCommand(workspace, surface, "Centerline Profile", [[0, 0], [15, 15], [30, 30]], interval=10.0)
profile.execute()
assert profile.record["stationing_metadata"]["length"] > 40.0
assert profile.record["samples"]

visual = site.visualization_metadata()
for key in ("grade_visualization", "cut_fill_visualization", "slope_visualization", "drainage_overlays", "section_previews", "boundary_previews", "engineering_diagnostics"):
    assert key in visual

ValidateSiteEngineeringCommand(workspace).execute()
report = site.ensure_project().validation_report
assert report.valid is True
assert not report.issues
assert site.ensure_project().diagnostics.grading_operations >= 5
assert site.ensure_project().diagnostics.volume_reports == 1
assert site.ensure_project().diagnostics.slope_reports == 1
assert site.ensure_project().diagnostics.drainage_reports == 1
assert site.ensure_project().diagnostics.sections == 1
assert site.ensure_project().diagnostics.profiles == 1
assert site.ensure_project().diagnostics.boundaries == 2

serializer = ProjectSerializer()
project_path = tmp_dir / "site_engineering_project.json"
serializer.save(workspace, project_path)
restored = serializer.load(project_path)
restored_site = restored.gis_manager.terrain_manager.site_engineering_manager
assert len(restored_site.ensure_project().grading_operations) >= 5
assert restored_site.ensure_project().volume_reports[0]["name"] == "Pad Earthwork"
assert restored_site.ensure_project().drainage_reports
assert restored_site.ensure_project().profiles
assert restored_site.ensure_project().validation_report.valid is True

print("site-engineering-ok")

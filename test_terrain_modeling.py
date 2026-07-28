import json
import struct
from pathlib import Path

from engine.commands import (
    CreateGISProjectCommand,
    CreateTerrainProjectCommand,
    EditTerrainSurfaceCommand,
    GenerateTerrainBodyCommand,
    GenerateTerrainContoursCommand,
    ImportTerrainFileCommand,
    RebuildTerrainSurfaceCommand,
    ValidateTerrainProjectCommand,
)
from engine.storage.project import ProjectSerializer
from engine.workspace.workspace import Workspace


def write_ascii_grid(path):
    path.write_text(
        "\n".join(
            [
                "ncols 3",
                "nrows 3",
                "xllcorner 100.0",
                "yllcorner 200.0",
                "cellsize 5.0",
                "NODATA_value -9999",
                "10 11 12",
                "13 14 15",
                "16 17 18",
            ]
        ),
        encoding="utf-8",
    )
    return path


def write_xyz(path):
    path.write_text("0,0,1\n1,0,2\n0,1,3\n1,1,4\n2,1,5\n", encoding="utf-8")
    return path


def write_tin(path):
    path.write_text(
        json.dumps(
            {
                "name": "Real TIN",
                "points": [[0, 0, 0], [10, 0, 1], [0, 10, 2], [10, 10, 3]],
                "triangles": [[0, 1, 2], [1, 3, 2]],
            }
        ),
        encoding="utf-8",
    )
    return path


def write_pgm(path):
    path.write_text("P2\n# terrain height map\n3 2\n255\n0 64 128\n192 224 255\n", encoding="ascii")
    return path


def write_geotiff(path):
    width, height = 3, 2
    values = [10.0, 11.0, 12.0, 14.0, 15.0, 16.0]
    endian = "<"
    image_data = struct.pack(endian + "6f", *values)
    ifd_offset = 8
    entries = []
    extra = bytearray()

    def add_tag(tag, typ, count, value_bytes_or_int):
        if isinstance(value_bytes_or_int, bytes):
            offset = 8 + 2 + 11 * 12 + 4 + len(extra)
            extra.extend(value_bytes_or_int)
            value = offset
        else:
            value = value_bytes_or_int
        entries.append((tag, typ, count, value))

    add_tag(256, 4, 1, width)
    add_tag(257, 4, 1, height)
    add_tag(258, 3, 1, 32)
    add_tag(259, 3, 1, 1)
    add_tag(273, 4, 1, 8 + 2 + 11 * 12 + 4 + 24 + 48)
    add_tag(279, 4, 1, len(image_data))
    add_tag(339, 3, 1, 3)
    add_tag(33550, 12, 3, struct.pack(endian + "3d", 2.0, 2.0, 1.0))
    add_tag(33922, 12, 6, struct.pack(endian + "6d", 0.0, 0.0, 0.0, 500.0, 900.0, 0.0))
    add_tag(277, 3, 1, 1)
    add_tag(284, 3, 1, 1)

    header = bytearray(b"II")
    header.extend(struct.pack(endian + "H", 42))
    header.extend(struct.pack(endian + "I", ifd_offset))
    ifd = bytearray(struct.pack(endian + "H", len(entries)))
    for entry in sorted(entries):
        ifd.extend(struct.pack(endian + "HHII", *entry))
    ifd.extend(struct.pack(endian + "I", 0))
    path.write_bytes(bytes(header + ifd + extra + image_data))
    return path


tmp_dir = Path(".tmp_test_output/terrain_modeling")
tmp_dir.mkdir(parents=True, exist_ok=True)

workspace = Workspace()
CreateGISProjectCommand(workspace, "GIS Site").execute()
CreateTerrainProjectCommand(workspace, "Production Terrain").execute()
terrain = workspace.gis_manager.terrain_manager

paths = [
    write_ascii_grid(tmp_dir / "terrain.asc"),
    write_ascii_grid(tmp_dir / "terrain.dem"),
    write_xyz(tmp_dir / "points.xyz"),
    write_tin(tmp_dir / "surface.tin"),
    write_pgm(tmp_dir / "heightmap.pgm"),
    write_geotiff(tmp_dir / "elevation.tif"),
]

surfaces = []
for index, path in enumerate(paths):
    command = ImportTerrainFileCommand(workspace, path, name=f"{path.stem}-{index}")
    command.execute()
    surfaces.append(command.surface)

assert len(terrain.ensure_project().surfaces) == 6
assert {surface.metadata["format"] for surface in surfaces} >= {"ASCII Grid", "XYZ Point Cloud", "TIN", "Height Map", "GeoTIFF"}
assert all(surface.points and surface.triangles for surface in surfaces)

grid_surface = surfaces[0]
previous = grid_surface.points[4][2]
raise_command = EditTerrainSurfaceCommand(workspace, grid_surface, "raise", {"bounds": [104, 204, 106, 206]}, amount=3.0)
raise_command.execute()
assert grid_surface.points[4][2] == previous + 3.0
raise_command.undo()
assert grid_surface.points[4][2] == previous
raise_command.execute()

EditTerrainSurfaceCommand(workspace, grid_surface, "lower", amount=1.0).execute()
EditTerrainSurfaceCommand(workspace, grid_surface, "flatten", {"bounds": [100, 200, 105, 205]}, elevation=20.0).execute()
EditTerrainSurfaceCommand(workspace, grid_surface, "smooth", strength=0.5).execute()
EditTerrainSurfaceCommand(workspace, grid_surface, "sculpt", {"center": [105.0, 205.0]}, amount=2.0, radius=8.0, strength=0.75).execute()
EditTerrainSurfaceCommand(workspace, grid_surface, "grade", {"start": [100, 200, 10], "end": [110, 210, 30]}).execute()
EditTerrainSurfaceCommand(workspace, grid_surface, "boundary", {"boundary": [[100, 200], [110, 200], [110, 210], [100, 210]]}).execute()
assert len(grid_surface.boundary) == 4

before_refine = len(grid_surface.points)
EditTerrainSurfaceCommand(workspace, grid_surface, "refine").execute()
assert len(grid_surface.points) > before_refine

rebuild = RebuildTerrainSurfaceCommand(workspace, grid_surface)
rebuild.execute()
assert grid_surface.triangles
rebuild.undo()
assert grid_surface.triangles == rebuild.before
rebuild.execute()

contours = GenerateTerrainContoursCommand(workspace, grid_surface, minor_interval=1.0, major_interval=5.0, smooth=True)
contours.execute()
assert terrain.ensure_project().contours
assert any(contour.contour_type == "Major" for contour in terrain.ensure_project().contours)

body_command = GenerateTerrainBodyCommand(workspace, grid_surface)
body_command.execute()
assert grid_surface.body_reference["source"] == "BodyManager"
assert workspace.product_manager.body_manager.visible_objects()
assert any(getattr(entity, "primitive_type", "") == "terrain" for entity in workspace.scene3d.entities())
body_command.undo()
assert not grid_surface.body_reference
body_command.execute()

assert isinstance(terrain.elevation_at(grid_surface, 105.0, 205.0), float)
assert terrain.slope_at(grid_surface, 105.0, 205.0) >= 0.0
assert 0.0 <= terrain.aspect_at(grid_surface, 105.0, 205.0) <= 360.0
stats = terrain.statistics(grid_surface)
assert stats["points"] == len(grid_surface.points)
assert stats["triangles"] == len(grid_surface.triangles)

visual = terrain.visualization_metadata()
for key in ("terrain_preview", "contours", "elevation_colors", "wireframe", "shaded_terrain", "selection", "editing_previews", "lod_visualization"):
    assert key in visual

ValidateTerrainProjectCommand(workspace).execute()
report = terrain.ensure_project().validation_report
assert report.valid is True
assert not report.issues
assert terrain.ensure_project().diagnostics.surfaces == 6
assert terrain.ensure_project().diagnostics.contours == len(terrain.ensure_project().contours)
assert terrain.ensure_project().diagnostics.validation_issues == 0

serializer = ProjectSerializer()
project_path = tmp_dir / "terrain_project.json"
serializer.save(workspace, project_path)
restored = serializer.load(project_path)
restored_terrain = restored.gis_manager.terrain_manager
assert len(restored_terrain.ensure_project().surfaces) == 6
restored_surface = restored_terrain.ensure_project().surfaces[0]
assert restored_surface.body_reference["source"] == "BodyManager"
assert restored_terrain.ensure_project().contours
assert restored_terrain.ensure_project().diagnostics.surfaces == 6

print("Terrain Modeling regression passed")

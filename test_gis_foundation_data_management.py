import json
import struct
import zipfile
from pathlib import Path

from engine.commands import (
    AddSurveyPointCommand,
    CreateGISProjectCommand,
    ImportGISFileCommand,
    RefreshGISIndexesCommand,
    ValidateGISProjectCommand,
)
from engine.gis import GISCoordinate
from engine.storage.project import ProjectSerializer
from engine.workspace.workspace import Workspace


def write_point_shapefile(base_path):
    shp_path = base_path.with_suffix(".shp")
    dbf_path = base_path.with_suffix(".dbf")
    prj_path = base_path.with_suffix(".prj")
    x, y = -122.4194, 37.7749
    content = struct.pack("<i2d", 1, x, y)
    file_length_words = (100 + 8 + len(content)) // 2
    header = bytearray(100)
    struct.pack_into(">i", header, 0, 9994)
    struct.pack_into(">i", header, 24, file_length_words)
    struct.pack_into("<i", header, 28, 1000)
    struct.pack_into("<i", header, 32, 1)
    struct.pack_into("<4d", header, 36, x, y, x, y)
    record_header = struct.pack(">2i", 1, len(content) // 2)
    shp_path.write_bytes(bytes(header) + record_header + content)

    fields = [("NAME", "C", 20, 0), ("ELEV", "N", 10, 2)]
    header_length = 32 + len(fields) * 32 + 1
    record_length = 1 + sum(field[2] for field in fields)
    dbf = bytearray()
    dbf.extend(struct.pack("<BBBBIHH20x", 3, 126, 7, 22, 1, header_length, record_length))
    for name, field_type, length, decimal in fields:
        descriptor = bytearray(32)
        descriptor[: len(name)] = name.encode("ascii")
        descriptor[11] = ord(field_type)
        descriptor[16] = length
        descriptor[17] = decimal
        dbf.extend(descriptor)
    dbf.append(0x0D)
    dbf.extend(b" " + b"Benchmark".ljust(20) + b"15.50".rjust(10))
    dbf.append(0x1A)
    dbf_path.write_bytes(bytes(dbf))
    prj_path.write_text('GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984"]]', encoding="utf-8")

    return shp_path


tmp_dir = Path(".tmp_test_output/gis_foundation")
tmp_dir.mkdir(parents=True, exist_ok=True)

geojson_path = tmp_dir / "site.geojson"
geojson_path.write_text(
    json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "parcel-1",
                    "properties": {"name": "Parcel 1", "class": "Parcel"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-122.42, 37.77], [-122.41, 37.77], [-122.41, 37.78], [-122.42, 37.77]]],
                    },
                }
            ],
        }
    ),
    encoding="utf-8",
)

kml_text = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
  <Placemark><name>Site Axis</name><LineString><coordinates>-122.42,37.77,0 -122.41,37.78,5</coordinates></LineString></Placemark>
</Document></kml>"""
kml_path = tmp_dir / "axis.kml"
kml_path.write_text(kml_text, encoding="utf-8")
kmz_path = tmp_dir / "axis.kmz"
with zipfile.ZipFile(kmz_path, "w") as archive:
    archive.writestr("doc.kml", kml_text)

gpx_path = tmp_dir / "survey.gpx"
gpx_path.write_text(
    """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Kinematics Studio">
  <wpt lat="37.7750" lon="-122.4195"><ele>12.5</ele><name>BM-1</name></wpt>
  <trk><name>Boundary Walk</name><trkseg><trkpt lat="37.775" lon="-122.419"/><trkpt lat="37.776" lon="-122.418"/></trkseg></trk>
</gpx>""",
    encoding="utf-8",
)

csv_path = tmp_dir / "points.csv"
csv_path.write_text(
    "name,longitude,latitude,elevation,code\nCP-1,-122.4180,37.7760,11.2,CONTROL\nCP-2,-122.4175,37.7765,11.6,CONTROL\n",
    encoding="utf-8",
)

shp_path = write_point_shapefile(tmp_dir / "benchmarks")

workspace = Workspace()
manager = workspace.gis_manager
workspace.command_manager.execute(CreateGISProjectCommand(workspace, "Release 2.0 GIS Foundation", "EPSG:4326"))
manager.initialize("Release 2.0 GIS Foundation", "EPSG:4326", metadata={"site": "Production GIS"})

utm = manager.coordinate_systems.transform(GISCoordinate(-122.4194, 37.7749, 0.0, "EPSG:4326"), "EPSG:32610")
round_trip = manager.coordinate_systems.transform(utm, "EPSG:4326")
assert abs(round_trip.x + 122.4194) < 0.00001
assert abs(round_trip.y - 37.7749) < 0.00001
ecef = manager.coordinate_systems.transform(GISCoordinate(-122.4194, 37.7749, 10.0, "EPSG:4326"), "EPSG:4978")
assert abs(ecef.x) > 1000000

for path, layer_name in (
    (geojson_path, "GeoJSON Site"),
    (shp_path, "Shapefile Benchmarks"),
    (kml_path, "KML Axis"),
    (kmz_path, "KMZ Axis"),
    (gpx_path, "GPX Survey"),
):
    workspace.command_manager.execute(ImportGISFileCommand(workspace, str(path), layer_name))
workspace.command_manager.execute(ImportGISFileCommand(workspace, str(csv_path), import_as_survey=True))
workspace.command_manager.execute(AddSurveyPointCommand(workspace, "BM Manual", -122.416, 37.777, 10.0, "EPSG:4326", "Benchmark"))
workspace.command_manager.execute(RefreshGISIndexesCommand(workspace))
workspace.command_manager.execute(ValidateGISProjectCommand(workspace))

project = manager.active_project
diagnostics = manager.diagnostics_report()
visualization = manager.visualization_metadata()

assert project.validation_report.valid, project.validation_report.issues
assert diagnostics.layers == 6
assert diagnostics.features >= 8
assert diagnostics.survey_points == 3
assert diagnostics.imports == 6
assert project.indexes["features"]
assert project.indexes["spatial"]
assert visualization["gis_layers"]
assert visualization["survey_points"]
assert visualization["coordinate_grids"]["project_crs"] == "EPSG:4326"
assert workspace.scene3d.entities() == []
assert workspace.command_manager.undo_count >= 10

validation_report = project.validation_report
workspace.command_manager.undo()
assert manager.active_project.validation_report is not validation_report
workspace.command_manager.redo()
assert manager.active_project.validation_report.valid

project_file = tmp_dir / "gis_project.ksproj"
serializer = ProjectSerializer()
serializer.save(workspace, project_file)
restored_workspace = serializer.load(project_file)
restored_manager = restored_workspace.gis_manager
restored_project = restored_manager.active_project

assert restored_project.name == "Release 2.0 GIS Foundation"
assert len(restored_project.layers) == 6
assert len(restored_project.import_records) == 6
assert restored_manager.validate_project().valid
assert restored_workspace.scene3d.entities() == []

print("gis-foundation-data-management-ok")

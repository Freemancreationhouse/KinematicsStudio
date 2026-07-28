import json
import sqlite3
import struct
import zipfile
from pathlib import Path

from engine.commands import (
    AddParcelCommand,
    AddRoadCommand,
    AddSurveyAlignmentCommand,
    AddUtilityNetworkCommand,
    CreateGISProjectCommand,
    CreateInfrastructureProjectCommand,
    CreateSiteEngineeringProjectCommand,
    CreateTerrainProjectCommand,
    EditRoadCommand,
    ImportGeoPackageCommand,
    ImportOpenStreetMapCommand,
    SynchronizeInfrastructureGISCommand,
    ValidateInfrastructureCommand,
)
from engine.storage.project import ProjectSerializer
from engine.workspace.workspace import Workspace


def write_polyline_shapefile(base_path):
    shp_path = base_path.with_suffix(".shp")
    dbf_path = base_path.with_suffix(".dbf")
    prj_path = base_path.with_suffix(".prj")
    points = [(0.0, 0.0), (20.0, 0.0), (30.0, 10.0)]
    content = bytearray()
    content.extend(struct.pack("<i4d2i", 3, 0.0, 0.0, 30.0, 10.0, 1, len(points)))
    content.extend(struct.pack("<i", 0))
    for point in points:
        content.extend(struct.pack("<2d", *point))
    header = bytearray(100)
    struct.pack_into(">i", header, 0, 9994)
    struct.pack_into(">i", header, 24, (100 + 8 + len(content)) // 2)
    struct.pack_into("<i", header, 28, 1000)
    struct.pack_into("<i", header, 32, 3)
    struct.pack_into("<4d", header, 36, 0.0, 0.0, 30.0, 10.0)
    shp_path.write_bytes(bytes(header) + struct.pack(">2i", 1, len(content) // 2) + bytes(content))
    fields = [("name", "C", 20, 0), ("highway", "C", 12, 0)]
    header_length = 32 + len(fields) * 32 + 1
    record_length = 1 + sum(field[2] for field in fields)
    dbf = bytearray(struct.pack("<BBBBIHH20x", 3, 126, 7, 22, 1, header_length, record_length))
    for name, field_type, length, decimal in fields:
        descriptor = bytearray(32)
        descriptor[: len(name)] = name.encode("ascii")
        descriptor[11] = ord(field_type)
        descriptor[16] = length
        descriptor[17] = decimal
        dbf.extend(descriptor)
    dbf.append(0x0D)
    dbf.extend(b" " + b"Shape Road".ljust(20) + b"collector".ljust(12))
    dbf.append(0x1A)
    dbf_path.write_bytes(bytes(dbf))
    prj_path.write_text('GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984"]]', encoding="utf-8")
    return shp_path


def wkb_linestring(points):
    raw = bytearray(b"\x01")
    raw.extend(struct.pack("<II", 2, len(points)))
    for point in points:
        raw.extend(struct.pack("<2d", point[0], point[1]))
    return bytes(raw)


def wkb_polygon(ring):
    raw = bytearray(b"\x01")
    raw.extend(struct.pack("<II", 3, 1))
    raw.extend(struct.pack("<I", len(ring)))
    for point in ring:
        raw.extend(struct.pack("<2d", point[0], point[1]))
    return bytes(raw)


def gpkg_blob(wkb):
    return b"GP" + bytes([0, 1]) + struct.pack("<I", 4326) + wkb


def write_geopackage(path):
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE gpkg_geometry_columns (table_name TEXT, column_name TEXT, geometry_type_name TEXT, srs_id INTEGER)")
    conn.execute("CREATE TABLE gpkg_spatial_ref_sys (srs_name TEXT, srs_id INTEGER, organization TEXT, organization_coordsys_id INTEGER, definition TEXT, description TEXT)")
    conn.execute("INSERT INTO gpkg_spatial_ref_sys VALUES ('WGS 84', 4326, 'EPSG', 4326, 'EPSG:4326', 'WGS 84')")
    conn.execute("CREATE TABLE road_features (id INTEGER PRIMARY KEY, name TEXT, highway TEXT, geom BLOB)")
    conn.execute("CREATE TABLE parcel_features (id INTEGER PRIMARY KEY, name TEXT, parcel TEXT, geom BLOB)")
    conn.execute("INSERT INTO gpkg_geometry_columns VALUES ('road_features', 'geom', 'LINESTRING', 4326)")
    conn.execute("INSERT INTO gpkg_geometry_columns VALUES ('parcel_features', 'geom', 'POLYGON', 4326)")
    conn.execute("INSERT INTO road_features VALUES (1, 'GPKG Road', 'primary', ?)", (gpkg_blob(wkb_linestring([[0, 0], [10, 10], [20, 10]])),))
    conn.execute("INSERT INTO parcel_features VALUES (1, 'GPKG Parcel', 'lot', ?)", (gpkg_blob(wkb_polygon([[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]])),))
    conn.commit()
    conn.close()
    return path


tmp_dir = Path(".tmp_test_output/infrastructure")
tmp_dir.mkdir(parents=True, exist_ok=True)

osm_path = tmp_dir / "site.osm"
osm_path.write_text(
    """<osm version="0.6">
<node id="1" lat="0.0" lon="0.0"/><node id="2" lat="0.0" lon="0.01"/><node id="3" lat="0.01" lon="0.01"/><node id="4" lat="0.01" lon="0.0"/>
<node id="5" lat="0.02" lon="0.0"/><node id="6" lat="0.02" lon="0.02"/>
<way id="100"><nd ref="1"/><nd ref="2"/><tag k="highway" v="residential"/><tag k="name" v="OSM Road"/></way>
<way id="200"><nd ref="1"/><nd ref="2"/><nd ref="3"/><nd ref="4"/><nd ref="1"/><tag k="landuse" v="residential"/><tag k="name" v="OSM Parcel"/></way>
<way id="300"><nd ref="5"/><nd ref="6"/><tag k="utility" v="water"/><tag k="name" v="OSM Water"/></way>
</osm>""",
    encoding="utf-8",
)
gpkg_path = write_geopackage(tmp_dir / "infrastructure.gpkg")
geojson_path = tmp_dir / "sync.geojson"
geojson_path.write_text(
    json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {"name": "GeoJSON Road", "highway": "service"}, "geometry": {"type": "LineString", "coordinates": [[0, 0], [5, 0], [8, 3]]}},
                {"type": "Feature", "properties": {"name": "GeoJSON Parcel", "parcel": "lot"}, "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]]]}}
            ],
        }
    ),
    encoding="utf-8",
)
kml_path = tmp_dir / "roads.kml"
kml_path.write_text(
    """<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><name>KML Road</name><ExtendedData><Data name="highway"><value>local</value></Data></ExtendedData><LineString><coordinates>0,0,0 1,1,0 2,1,0</coordinates></LineString></Placemark></Document></kml>""",
    encoding="utf-8",
)
kmz_path = tmp_dir / "roads.kmz"
with zipfile.ZipFile(kmz_path, "w") as archive:
    archive.writestr("doc.kml", kml_path.read_text(encoding="utf-8").replace("KML Road", "KMZ Road"))
shp_path = write_polyline_shapefile(tmp_dir / "shape_roads")

workspace = Workspace()
CreateGISProjectCommand(workspace, "GIS").execute()
CreateTerrainProjectCommand(workspace, "Terrain").execute()
CreateSiteEngineeringProjectCommand(workspace, "Site").execute()
CreateInfrastructureProjectCommand(workspace, "Infrastructure").execute()
infra = workspace.gis_manager.terrain_manager.site_engineering_manager.infrastructure_manager

road = AddRoadCommand(workspace, "Main Road", [[0, 0, 100], [50, 0, 101], [100, 25, 105]], lanes=[{"name": "EB", "width": 3.6}, {"name": "WB", "width": 3.6}], hierarchy="Arterial")
road.execute()
assert road.record["horizontal_alignment"]["length"] > 100.0
assert road.record["corridor"]["area"] > 0.0
edit = EditRoadCommand(workspace, road.record, centerline=[[0, 0], [40, 20], [100, 30]])
edit.execute()
assert road.record["centerline"][1] == [40.0, 20.0]
edit.undo()
assert road.record["centerline"][1] == [50.0, 0.0]

parcel = AddParcelCommand(workspace, "Lot 1", [[0, 0], [20, 0], [20, 15], [0, 15]], {"block": "A"}, {"owner": "Owner A"}, {"phase": "1"})
parcel.execute()
assert parcel.record["area"] == 300.0
parcel.undo()
assert not infra.ensure_project().parcels
parcel.execute()

utility = AddUtilityNetworkCommand(
    workspace,
    "Stormwater",
    "Storm Main",
    nodes=[{"id": "S1", "point": [0, 0]}, {"id": "S2", "point": [25, 0]}, {"id": "S3", "point": [25, 20]}],
    edges=[{"from": "S1", "to": "S2"}, {"from": "S2", "to": "S3"}],
    metadata={"diameter": 600},
)
utility.execute()
assert sum(edge["length"] for edge in utility.record["edges"]) == 45.0

alignment = AddSurveyAlignmentCommand(workspace, "Control Line", [[0, 0], [30, 0], [30, 40]])
alignment.execute()
assert alignment.record["stationing"][-1]["station"] == 70.0

osm = ImportOpenStreetMapCommand(workspace, osm_path)
osm.execute()
assert osm.record["counts"]["roads"] == 1
assert osm.record["counts"]["parcels"] == 1
assert osm.record["counts"]["utilities"] == 1

gpkg = ImportGeoPackageCommand(workspace, gpkg_path)
gpkg.execute()
assert gpkg.record["feature_count"] == 2

sync_geojson = SynchronizeInfrastructureGISCommand(workspace, geojson_path, "Infrastructure GeoJSON")
sync_geojson.execute()
assert sync_geojson.record["counts"]["roads"] >= 1
assert sync_geojson.record["counts"]["parcels"] >= 1
sync_shp = SynchronizeInfrastructureGISCommand(workspace, shp_path, "Infrastructure Shapefile")
sync_shp.execute()
assert sync_shp.record["counts"]["roads"] >= 1
sync_kml = SynchronizeInfrastructureGISCommand(workspace, kml_path, "Infrastructure KML")
sync_kml.execute()
assert sync_kml.record["counts"]["roads"] >= 1
sync_kmz = SynchronizeInfrastructureGISCommand(workspace, kmz_path, "Infrastructure KMZ")
sync_kmz.execute()
assert sync_kmz.record["counts"]["roads"] >= 1

visual = infra.visualization_metadata()
for key in ("roads", "parcels", "utilities", "survey_alignments", "infrastructure_overlays", "selection", "diagnostics"):
    assert key in visual

ValidateInfrastructureCommand(workspace).execute()
report = infra.ensure_project().validation_report
assert report.valid is True
assert not report.issues
assert infra.ensure_project().diagnostics.roads >= 6
assert infra.ensure_project().diagnostics.parcels >= 4
assert infra.ensure_project().diagnostics.utility_networks >= 2
assert infra.ensure_project().diagnostics.alignments == 1
assert infra.ensure_project().indexes["roads"]

serializer = ProjectSerializer()
project_path = tmp_dir / "infrastructure_project.json"
serializer.save(workspace, project_path)
restored = serializer.load(project_path)
restored_infra = restored.gis_manager.terrain_manager.site_engineering_manager.infrastructure_manager
assert restored_infra.ensure_project().roads
assert restored_infra.ensure_project().parcels
assert restored_infra.ensure_project().utility_networks
assert restored_infra.ensure_project().validation_report.valid is True

print("infrastructure-gis-integration-ok")

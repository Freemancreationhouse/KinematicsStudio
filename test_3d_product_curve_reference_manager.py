from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.product import CurveDefinition, ProductPart
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(4.0, 4.0, 4.0), name="Curve Reference Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Curve Reference Product")
part = manager.add_part(ProductPart("Curve Reference Part", "Curve Reference Mesh"))

definition = CurveDefinition(
    part.id,
    sketch_geometry_ids=["sketch-line-a"],
    mesh_entity_ids=["Curve Reference Mesh"],
    marker_points=[Vector3(0.0, 0.0, 0.0), Vector3(1.0, 0.0, 0.0), Vector3(2.0, 0.5, 0.0)],
)
spline = manager.curve_manager.create_curve("SplineCurve", part, definition, name="Guide Spline")
bezier = manager.curve_manager.create_curve("BezierCurve", part, CurveDefinition(part.id), name="Bezier")
nurbs = manager.curve_manager.create_curve("NURBSCurve", part, CurveDefinition(part.id), name="NURBS")
polyline = manager.curve_manager.create_curve("PolylineCurve", part, CurveDefinition(part.id), name="Polyline")
composite = manager.curve_manager.create_curve("CompositeCurve", part, CurveDefinition(part.id, reference_ids=[spline.id]), name="Composite")
helix = manager.curve_manager.create_curve("HelixCurve", part, CurveDefinition(part.id), name="Helix")
spiral = manager.curve_manager.create_curve("SpiralCurve", part, CurveDefinition(part.id), name="Spiral")
intersection = manager.curve_manager.create_curve("IntersectionCurve", part, CurveDefinition(part.id, body_ids=["body-a"]), name="Intersection")
projected = manager.curve_manager.create_curve("ProjectedCurve", part, CurveDefinition(part.id, reference_ids=[spline.id]), name="Projected")

plane = manager.reference_geometry_manager.create_plane(part, "Offset Plane", [mesh.name])
axis = manager.reference_geometry_manager.create_axis(part, "Axis through Two Points", [spline.id])
point = manager.reference_geometry_manager.create_point(part, "Point on Curve", [spline.id])
coord = manager.reference_geometry_manager.create_coordinate_system(part, [plane.id, axis.id])
group = manager.reference_geometry_manager.create_group(part, [plane.id, axis.id, point.id])

construction_plane = manager.construction_geometry_manager.create("ConstructionPlane", part, [plane.id])
construction_axis = manager.construction_geometry_manager.create("ConstructionAxis", part, [axis.id])
construction_point = manager.construction_geometry_manager.create("ConstructionPoint", part, [point.id])
construction_sketch = manager.construction_geometry_manager.create("ConstructionSketchReference", part, ["sketch-line-a"])

curve_stats = manager.curve_manager.statistics()
reference_stats = manager.reference_geometry_manager.statistics()
construction_stats = manager.construction_geometry_manager.statistics()

assert spline.type_name == "SplineCurve"
assert bezier.type_name == "BezierCurve"
assert nurbs.type_name == "NURBSCurve"
assert polyline.type_name == "PolylineCurve"
assert composite.type_name == "CompositeCurve"
assert helix.type_name == "HelixCurve"
assert spiral.type_name == "SpiralCurve"
assert intersection.type_name == "IntersectionCurve"
assert projected.type_name == "ProjectedCurve"
assert curve_stats.curves == 9
assert curve_stats.placeholders == 2
assert reference_stats.references == 5
assert reference_stats.planes == 1
assert reference_stats.axes == 1
assert reference_stats.points == 1
assert reference_stats.coordinate_systems == 1
assert reference_stats.groups == 1
assert construction_stats.construction_items == 4
assert construction_plane.type_name == "ConstructionPlane"
assert construction_axis.type_name == "ConstructionAxis"
assert construction_point.type_name == "ConstructionPoint"
assert construction_sketch.type_name == "ConstructionSketchReference"
assert len(manager.curves_for(part)) == 9
assert len(manager.reference_geometry_for(part)) == 5
assert len(manager.construction_geometry_for(part)) == 4
assert len(manager.dependency_edges) >= 10

print("3d-product-curve-reference-manager-ok")

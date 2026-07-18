import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.product import CurveDefinition, ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(3.0, 3.0, 3.0), name="Persisted Curve Reference Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted Curve Reference Product")
part = manager.add_part(ProductPart("Persisted Curve Reference Part", "Persisted Curve Reference Mesh"))
curve = manager.curve_manager.create_curve(
    "HelixCurve",
    part,
    CurveDefinition(part.id, mesh_entity_ids=["Persisted Curve Reference Mesh"], marker_points=[Vector3(0, 0, 0), Vector3(0, 0, 1)]),
    name="Persisted Helix",
)
reference = manager.reference_geometry_manager.create_plane(part, "Plane through 3 Points", [curve.id])
construction = manager.construction_geometry_manager.create("ConstructionSketchReference", part, [curve.id], "Persisted Construction Sketch Ref")
workspace.selection.select(construction)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "curve_reference.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.curves[0].type_name == "HelixCurve"
    assert len(restored.curves[0].definition.marker_points) == 2
    assert restored.reference_geometry[0].type_name == "ReferencePlane"
    assert restored.reference_geometry[0].metadata.reference_type == "Plane through 3 Points"
    assert restored.construction_geometry[0].type_name == "ConstructionSketchReference"
    assert restored.construction_geometry[0].selected is True
    assert restored.curve_statistics.helices == 1
    assert restored.reference_geometry_statistics.planes == 1
    assert restored.construction_statistics.sketch_references == 1

print("3d-product-curve-reference-persistence-ok")

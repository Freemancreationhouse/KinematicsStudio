import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart, SurfaceFeatureOptions, SurfaceFeatureDefinition


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(8.0, 1.0, 8.0), name="Persisted Surface Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted Surface Product")
part = manager.add_part(ProductPart("Persisted Surface Part", "Persisted Surface Mesh"))
surface_body = manager.surface_manager.create_surface_body(part, "Persisted Surface Mesh", "Persisted Surface Body")

loft = manager.feature_manager.create_feature("Loft Surface", part, body=surface_body)
loft.surface_definition = SurfaceFeatureDefinition(
    "Loft Surface",
    target_surface_ids=[surface_body.id],
    options=SurfaceFeatureOptions(profile_ids=["a", "b", "c"]),
)
trim = manager.surface_operation_manager.create_operation("Trim", part, surface_body)
manager.feature_manager.apply_feature(loft, workspace)
manager.feature_manager.apply_feature(trim, workspace)
workspace.selection.select(trim)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "surface_foundation.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.surface_bodies[0].type_name == "SurfaceBody"
    assert restored.features[0].type_name == "LoftSurfaceFeature"
    assert restored.features[1].type_name == "TrimSurfaceFeature"
    assert restored.features[0].surface_definition.options.profile_ids == ["a", "b", "c"]
    assert restored.surface_operation_metadata[0].operation_type == "Trim"
    assert restored.surface_statistics.surface_bodies == 1
    assert restored.surface_operation_statistics.trim == 1
    assert restored.features[1].selected is True

print("3d-product-surface-foundation-persistence-ok")
